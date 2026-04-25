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
        if not text or text == self._last_text:
            return
        self._last_text = text
        self._queue.put(text)

    def toggle(self) -> None:
        self.enabled = not self.enabled
        if self.enabled and self._engine is None:
            self._init_engine()

    def stop(self) -> None:
        self._stop_event.set()


class SentenceBuilder:
    def __init__(
        self,
        stable_frames: int = 6,
        min_confidence: float = 0.6,
        commit_cooldown: float = 0.5,
        repeat_delay: float = 1.2,
        space_timeout: float = 1.0,
        sentence_timeout: float = 2.5,
    ) -> None:
        self.stable_frames = stable_frames
        self.min_confidence = min_confidence
        self.commit_cooldown = commit_cooldown
        self.repeat_delay = repeat_delay
        self.space_timeout = space_timeout
        self.sentence_timeout = sentence_timeout

        self._buffer = []
        self._current_label = None
        self._stable_count = 0
        self._last_commit_time = 0.0
        self._last_committed_label = None

        self._last_hand_time = 0.0
        self._space_inserted = False
        self._sentence_inserted = False

    @property
    def text(self) -> str:
        return "".join(self._buffer)

    def clear(self) -> None:
        self._buffer = []
        self._current_label = None
        self._stable_count = 0
        self._last_commit_time = 0.0
        self._last_committed_label = None
        self._space_inserted = False
        self._sentence_inserted = False

    def backspace(self) -> None:
        if self._buffer:
            self._buffer.pop()

    def append_punctuation(self, ch: str) -> None:
        if ch not in [".", "!", "?", ","]:
            return
        while self._buffer and self._buffer[-1] == " ":
            self._buffer.pop()
        if self._buffer and self._buffer[-1] in [".", "!", "?", ","]:
            return
        self._buffer.append(ch)
        self._buffer.append(" ")

    def _append_char(self, ch: str) -> None:
        if ch == " ":
            if not self._buffer or self._buffer[-1] == " ":
                return
        if ch in [".", "!", "?"]:
            while self._buffer and self._buffer[-1] == " ":
                self._buffer.pop()
            if self._buffer and self._buffer[-1] in [".", "!", "?"]:
                return
        self._buffer.append(ch)

    def _append_text(self, text: str) -> None:
        for ch in text:
            self._append_char(ch)

    def update(self, label: str, confidence: float, has_hand: bool, now: float):
        event = {"word_complete": None, "sentence_complete": None, "char_added": None}

        if has_hand:
            self._last_hand_time = now
            self._space_inserted = False
            self._sentence_inserted = False

            if label == self._current_label:
                self._stable_count += 1
            else:
                self._current_label = label
                self._stable_count = 1

            if self._stable_count >= self.stable_frames and confidence >= self.min_confidence:
                can_repeat = (label != self._last_committed_label) or (
                    now - self._last_commit_time >= self.repeat_delay
                )
                if (now - self._last_commit_time) >= self.commit_cooldown and can_repeat:
                    self._append_char(label)
                    self._last_commit_time = now
                    self._last_committed_label = label
                    event["char_added"] = label
        else:
            if self._last_hand_time > 0:
                idle = now - self._last_hand_time
                if idle >= self.sentence_timeout and not self._sentence_inserted:
                    self._append_text(". ")
                    self._sentence_inserted = True
                    self._space_inserted = True
                    event["sentence_complete"] = self.text.strip()
                elif idle >= self.space_timeout and not self._space_inserted:
                    self._append_char(" ")
                    self._space_inserted = True
                    words = self.text.strip().split()
                    if words:
                        event["word_complete"] = words[-1]

            self._current_label = None
            self._stable_count = 0

        return event


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time ASL sentence translator using MediaPipe + TensorFlow.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--model", type=str, default="models/asl_mlp.keras")
    parser.add_argument("--encoder", type=str, default="models/label_encoder.pkl")
    parser.add_argument("--smoothing", type=int, default=7)
    parser.add_argument("--confidence", type=float, default=0.6)
    parser.add_argument("--stable-frames", type=int, default=6)
    parser.add_argument("--space-timeout", type=float, default=1.0, help="Pause to insert space")
    parser.add_argument("--sentence-timeout", type=float, default=2.5, help="Longer pause to end sentence")
    parser.add_argument("--tts", action="store_true", help="Enable text-to-speech")
    parser.add_argument("--speak-mode", type=str, default="sentence", choices=["off", "word", "sentence"])
    args = parser.parse_args()

    predictor = SignLanguagePredictor(
        model_path=args.model,
        encoder_path=args.encoder,
        smoothing_window=args.smoothing,
    )
    tts = TextToSpeech(enabled=args.tts)

    builder = SentenceBuilder(
        stable_frames=args.stable_frames,
        min_confidence=args.confidence,
        space_timeout=args.space_timeout,
        sentence_timeout=args.sentence_timeout,
    )

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
                label_text = f"{label} ({confidence:.2f})"
                event = builder.update(label, confidence, True, time.time())
            else:
                event = builder.update("", 0.0, False, time.time())
                predictor.reset()

            if args.speak_mode != "off" and tts.enabled:
                if args.speak_mode == "word" and event["word_complete"]:
                    tts.speak(event["word_complete"])
                if args.speak_mode == "sentence" and event["sentence_complete"]:
                    tts.speak(event["sentence_complete"])

            sentence_text = builder.text
            if len(sentence_text) > 80:
                sentence_text = "..." + sentence_text[-80:]

            current_time = time.time()
            fps = 1.0 / max(current_time - prev_time, 1e-6)
            prev_time = current_time

            draw_label(frame, label_text, position=(10, 40))
            draw_label(frame, f"Sentence: {sentence_text}", position=(10, 80), scale=0.6, thickness=1)
            draw_label(
                frame,
                f"TTS: {'ON' if tts.enabled else 'OFF'} (T) | Clear (C) | Backspace (B) | . , ! ? keys",
                position=(10, 110),
                scale=0.5,
                thickness=1,
            )
            draw_fps(frame, fps, position=(10, 140))

            cv2.imshow("ASL Sentence Translator", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("t"):
                tts.toggle()
            if key == ord("c"):
                builder.clear()
            if key in (ord("b"), 8):
                builder.backspace()
            if key in (ord("."), ord(","), ord("!"), ord("?")):
                builder.append_punctuation(chr(key))

    tts.stop()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
