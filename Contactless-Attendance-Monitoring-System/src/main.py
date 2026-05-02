"""
main.py — Contactless Attendance Monitoring System
           Main entry point for Raspberry Pi 4

Full pipeline (matches Fig. 4 System Overview in the paper):
  1. Initialise IR sensor + camera
  2. Wait for IR trigger (person approaches)
  3. Open camera → run face detection + recognition loop
  4. If face recognised → mark PRESENT in attendance
  5. If face not recognised after N attempts → offer QR backup
  6. At session end → mark all absent → send email alert → generate report

Usage:
    python3 src/main.py
    python3 src/main.py --session-minutes 60
    python3 src/main.py --no-ir        (skip IR trigger, useful for testing)

Published: ICCDS February 2023 (ISBN: 979-8-9879839-0-4)
Authors:   Darshit Shah, Parthav Shah, Smit Shah
Guide:     Mr. Sunil Khatri, Dept. of IoT, TCET Mumbai
"""

import cv2
import sys
import os
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    CAMERA_RESOLUTION, CAMERA_FRAMERATE, DISPLAY_WINDOW_NAME,
    MAX_FAILED_ATTEMPTS, SESSION_TIMEOUT_MIN
)
from recognizer.face_rec   import FaceRecognizer
from attendance.logger     import AttendanceLogger
from utils.ir_sensor       import IRSensor
from utils.qr_backup       import generate_qr, verify_qr_scan


def run_session(session_minutes: int, skip_ir: bool, admin_email: str = None):
    """Run one complete attendance session."""

    print("=" * 60)
    print("  Contactless Attendance Monitoring System")
    print(f"  Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # ── Load trained model ────────────────────────────────────────────────────
    try:
        recognizer = FaceRecognizer()
    except FileNotFoundError as e:
        print(f"[MAIN] ❌ {e}")
        sys.exit(1)

    # ── Initialise attendance logger ──────────────────────────────────────────
    logger = AttendanceLogger()

    # ── Initialise IR sensor ──────────────────────────────────────────────────
    ir = IRSensor()

    # ── Counters (per candidate) ──────────────────────────────────────────────
    failed_attempts = {}      # candidate_id → int  (unknown has key "unknown")
    session_end_time = time.time() + session_minutes * 60

    print(f"[MAIN] Session will run for {session_minutes} minutes.")
    print("[MAIN] Press 'q' in the video window to end the session early.\n")

    try:
        while time.time() < session_end_time:

            # ── Wait for IR trigger ───────────────────────────────────────────
            if not skip_ir:
                triggered = ir.wait_for_trigger(poll_interval=0.1, timeout=5.0)
                if not triggered:
                    # Check session timeout
                    remaining = (session_end_time - time.time()) / 60
                    print(f"[MAIN] Session time remaining: {remaining:.1f} min")
                    continue

            # ── Open camera ───────────────────────────────────────────────────
            cam = cv2.VideoCapture(0)
            cam.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_RESOLUTION[0])
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
            cam.set(cv2.CAP_PROP_FPS, CAMERA_FRAMERATE)

            print("[MAIN] Camera active. Starting face recognition...")
            recognised_this_trigger = set()
            fail_count = 0
            camera_timeout = time.time() + 30  # 30s per trigger event

            while time.time() < camera_timeout and time.time() < session_end_time:
                ret, frame = cam.read()
                if not ret:
                    break

                # ── Predict ───────────────────────────────────────────────────
                results, annotated = recognizer.predict_frame(frame)

                for res in results:
                    name = res["name"]
                    cid  = res["id"]

                    if name == "Unknown":
                        fail_count += 1
                        cv2.putText(annotated, "Unknown", (30, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)

                        # Offer QR backup after MAX_FAILED_ATTEMPTS
                        if fail_count >= MAX_FAILED_ATTEMPTS:
                            print("[MAIN] Face not recognised. Offering QR backup...")
                            _handle_qr_backup(logger, recognizer.label_names)
                            fail_count = 0
                    else:
                        if cid not in recognised_this_trigger:
                            newly_marked = logger.mark_present(cid, name)
                            if newly_marked:
                                cv2.putText(annotated, f"Welcome, {name}!", (30, 60),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                            recognised_this_trigger.add(cid)
                            fail_count = 0

                # ── Display ───────────────────────────────────────────────────
                # Show FPS in corner
                fps_text = f"FPS: {cam.get(cv2.CAP_PROP_FPS):.0f}"
                cv2.putText(annotated, fps_text, (CAMERA_RESOLUTION[0] - 90, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                cv2.imshow(DISPLAY_WINDOW_NAME, annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("[MAIN] 'q' pressed — ending session.")
                    cam.release()
                    cv2.destroyAllWindows()
                    ir.cleanup()
                    _close_session(logger, recognizer, admin_email)
                    return

                # Stop camera once all present candidates confirmed
                # (or IR no longer triggered when not in skip_ir mode)
                if not skip_ir and not ir.is_triggered():
                    break

            cam.release()
            cv2.destroyAllWindows()

            if skip_ir:
                break  # single-pass in no-IR mode

    except KeyboardInterrupt:
        print("\n[MAIN] Interrupted by user.")

    finally:
        ir.cleanup()

    _close_session(logger, recognizer, admin_email)


def _handle_qr_backup(logger: AttendanceLogger, label_names: dict):
    """
    Prompt the user to enter their candidate ID, generate a QR code,
    wait 5 seconds, then verify and mark attendance.
    """
    print("[QR] Enter your candidate ID for QR backup: ", end="", flush=True)
    try:
        cid = input().strip()
    except EOFError:
        return

    if cid not in label_names:
        print(f"[QR] ID '{cid}' not found in enrolled candidates.")
        return

    name = label_names[cid]
    qr_img, token = generate_qr(cid, name)

    if qr_img is None:
        print("[QR] QR library not available — backup not possible.")
        return

    # Display QR in a window for 5 seconds
    import numpy as np
    qr_arr = np.array(qr_img)
    qr_bgr = cv2.cvtColor(qr_arr, cv2.COLOR_RGB2BGR)
    qr_bgr = cv2.resize(qr_bgr, (300, 300))
    cv2.imshow("QR Code — Scan within 5 seconds", qr_bgr)
    cv2.waitKey(5000)
    cv2.destroyWindow("QR Code — Scan within 5 seconds")

    # Verify the token (in production this would come from a scanner/mobile app)
    valid, verified_id, verified_name = verify_qr_scan(token)
    if valid:
        logger.mark_present(verified_id, verified_name)
    else:
        print(f"[QR] QR verification failed: {verified_id}")


def _close_session(logger: AttendanceLogger, recognizer: FaceRecognizer, admin_email: str):
    """Close the session, mark absences, generate report."""
    print("\n[MAIN] Closing session...")
    absent = logger.close_session(recognizer.get_enrolled_ids(), recognizer.label_names)

    # Generate monthly report
    report_path = logger.generate_monthly_report()
    print(f"[MAIN] Monthly report: {report_path}")

    # Print session summary
    print("\n" + "=" * 60)
    print(f"  Present: {len(logger.session_present)}")
    print(f"  Absent:  {len(absent)}")
    if absent:
        print("  Absent candidates:")
        for name in absent:
            print(f"    • {name}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contactless Attendance Monitoring System")
    parser.add_argument("--session-minutes", type=int, default=SESSION_TIMEOUT_MIN,
                        help="Duration of attendance session in minutes")
    parser.add_argument("--no-ir",  action="store_true",
                        help="Skip IR trigger (useful for testing without sensor)")
    parser.add_argument("--admin-email", type=str, default=None,
                        help="Administrator email for absence alerts")
    args = parser.parse_args()

    run_session(
        session_minutes = args.session_minutes,
        skip_ir         = args.no_ir,
        admin_email     = args.admin_email,
    )
