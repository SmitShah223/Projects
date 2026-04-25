import argparse
import csv
import os
import sys
import time
from typing import Dict
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from utils.mediapipe_utils import create_hands, draw_hand_landmarks, extract_hands, select_primary_hand
from utils.visualization import draw_label


def build_header() -> list:
    header = ["label", "handedness"]
    for idx in range(21):
        header.extend([f"lm{idx}_x", f"lm{idx}_y", f"lm{idx}_z"])
    return header


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ASL hand landmark data using MediaPipe Hands.")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Directory to store raw CSV files")
    parser.add_argument("--min-detection", type=float, default=0.6, help="MediaPipe min detection confidence")
    parser.add_argument("--min-tracking", type=float, default=0.6, help="MediaPipe min tracking confidence")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(args.output_dir, f"collection_{timestamp}.csv")
    #output_path = os.path.join(args.output_dir, "collection_20260204_150717.csv")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Check the camera index.")

    counts: Dict[str, int] = {}
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(build_header())

        with create_hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=args.min_detection,
            min_tracking_confidence=args.min_tracking,
        ) as hands:

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                hands_data = extract_hands(results)
                primary_hand = select_primary_hand(hands_data)

                if primary_hand is not None:
                    draw_hand_landmarks(frame, primary_hand["raw"])

                instruction = "Press A-Z to label, Q to quit"
                draw_label(frame, instruction, position=(10, 30))

                if counts:
                    latest = sorted(counts.items(), key=lambda x: x[0])
                    counts_text = " ".join([f"{k}:{v}" for k, v in latest])
                    draw_label(frame, counts_text, position=(10, 70), scale=0.6, thickness=1)

                cv2.imshow("ASL Data Collection", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == 27:  # ESC only
                    break

                if key == 59:
                    label = "Q"
                    if primary_hand is None:
                        continue
                    landmarks = primary_hand["landmarks"].flatten().tolist()
                    row = [label, primary_hand["handedness"]] + landmarks
                    writer.writerow(row)
                    csvfile.flush()
                    counts[label] = counts.get(label, 0) + 1


                if 65 <= key <= 90 or 97 <= key <= 122:
                    label = chr(key).upper()
                    if primary_hand is None:
                        continue
                    landmarks = primary_hand["landmarks"].flatten().tolist()
                    row = [label, primary_hand["handedness"]] + landmarks
                    writer.writerow(row)
                    csvfile.flush()
                    counts[label] = counts.get(label, 0) + 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"Saved data to {output_path}")


if __name__ == "__main__":
    main()
