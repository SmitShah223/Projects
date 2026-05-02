"""
dataset/capture.py — Capture face dataset for a new candidate.

Steps (matches paper Section II-A):
  1. Detect IR trigger (or run directly for enrollment)
  2. Open camera, use Haar Cascade to detect face
  3. Capture FRAMES_PER_CANDIDATE frames with varying expressions/angles
  4. Save as grayscale images: dataset/<candidate_id>/<candidate_id>_0001.jpg

Usage:
    python3 src/dataset/capture.py --name "Smit Shah" --id 23

Dependencies (install via pip3):
    opencv-python  numpy
"""

import cv2
import os
import sys
import argparse
import time

# Allow running as standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HAAR_CASCADE_PATH, DATASET_DIR, FRAMES_PER_CANDIDATE, CAPTURE_DELAY_MS, CAMERA_RESOLUTION

def capture_dataset(candidate_id: int, candidate_name: str) -> None:
    """
    Capture FRAMES_PER_CANDIDATE face images for a candidate.

    Args:
        candidate_id   : Unique integer ID for this candidate (e.g. roll number)
        candidate_name : Display name (used to create the folder)
    """
    # ── Folder setup ─────────────────────────────────────────────────────────
    save_dir = os.path.join(DATASET_DIR, f"{candidate_id}_{candidate_name.replace(' ', '_')}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"[CAPTURE] Saving dataset to: {save_dir}")

    # ── Load Haar Cascade ────────────────────────────────────────────────────
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    if face_cascade.empty():
        raise FileNotFoundError(f"Haar cascade not found at {HAAR_CASCADE_PATH}. "
                                "Install with: sudo apt install python3-opencv")

    # ── Open camera ──────────────────────────────────────────────────────────
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_RESOLUTION[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])

    if not cam.isOpened():
        raise RuntimeError("Cannot open camera. Check CSI connection on Raspberry Pi.")

    print(f"[CAPTURE] Starting capture for: {candidate_name} (ID: {candidate_id})")
    print("[CAPTURE] Look at the camera. Vary your expression and angle slightly.")
    print(f"[CAPTURE] Capturing {FRAMES_PER_CANDIDATE} frames... Press 'q' to quit.")

    count = 0
    while count < FRAMES_PER_CANDIDATE:
        ret, frame = cam.read()
        if not ret:
            print("[CAPTURE] Camera read failed.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces using Haar Cascade
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor  = 1.1,
            minNeighbors = 5,
            minSize      = (100, 100),
        )

        for (x, y, w, h) in faces:
            count += 1
            face_roi = gray[y:y+h, x:x+w]
            filename = os.path.join(save_dir, f"{candidate_id}_{count:04d}.jpg")
            cv2.imwrite(filename, face_roi)

            # Draw rectangle on display
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"{count}/{FRAMES_PER_CANDIDATE}",
                        (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Capture — press q to quit", frame)

        if cv2.waitKey(CAPTURE_DELAY_MS) & 0xFF == ord('q'):
            print("[CAPTURE] Aborted by user.")
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"[CAPTURE] ✅ Done. {count} frames saved to {save_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture face dataset for a candidate.")
    parser.add_argument("--id",   type=int, required=True, help="Candidate ID (e.g. roll number)")
    parser.add_argument("--name", type=str, required=True, help="Candidate name (e.g. 'Smit Shah')")
    args = parser.parse_args()
    capture_dataset(args.id, args.name)
