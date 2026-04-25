import argparse
import os
import sys
import time
import threading
import queue

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from inference.predictor import SignLanguagePredictor
from utils.mediapipe_utils import create_hands, draw_hand_landmarks, extract_hands, select_primary_hand
from utils.visualization import draw_label, draw_fps


class TextToSpeech:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self._engine = None
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._last_text = ""
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        if enabled:
            self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        except Exception:
            self._engine = None
            self.enabled = False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if self._engine is None:
                continue
            self._engine.say(text)
            self._engine.runAndWait()

    def speak(self, text: str) -> None:
        if not self.enabled or self._engine is None:
            return
        if text == self._last_text:
            return
        self._last_text = text
        self._queue.put(text)

    def toggle(self) -> None:
        self.enabled = not self.enabled
        if self.enabled and self._engine is None:
            self._init_engine()

    def stop(self) -> None:
        self._stop_event.set()


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time ASL translator using MediaPipe + TensorFlow.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--model", type=str, default="models/asl_mlp.keras")
    parser.add_argument("--encoder", type=str, default="models/label_encoder.pkl")
    parser.add_argument("--smoothing", type=int, default=7)
    parser.add_argument("--confidence", type=float, default=0.6)
    parser.add_argument("--tts", action="store_true", help="Enable text-to-speech")
    args = parser.parse_args()

    predictor = SignLanguagePredictor(
        model_path=args.model,
        encoder_path=args.encoder,
        smoothing_window=args.smoothing,
    )
    tts = TextToSpeech(enabled=args.tts)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Check the camera index.")

    prev_time = time.time()

    with create_hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
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

            label_text = "No hand detected"
            if primary_hand is not None:
                draw_hand_landmarks(frame, primary_hand["raw"])
                label, confidence = predictor.predict(
                    primary_hand["landmarks"], primary_hand["handedness"]
                )
                if confidence >= args.confidence:
                    label_text = f"{label} ({confidence:.2f})"
                    tts.speak(label)
                else:
                    label_text = f"Uncertain ({confidence:.2f})"
            else:
                predictor.reset()

            current_time = time.time()
            fps = 1.0 / max(current_time - prev_time, 1e-6)
            prev_time = current_time

            draw_label(frame, label_text, position=(10, 40))
            draw_label(
                frame,
                f"TTS: {'ON' if tts.enabled else 'OFF'} (press T to toggle)",
                position=(10, 80),
                scale=0.6,
                thickness=1,
            )
            draw_fps(frame, fps, position=(10, 110))

            cv2.imshow("ASL Real-time Translator", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("t"),):
                tts.toggle()

    tts.stop()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
