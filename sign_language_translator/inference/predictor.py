import os
import sys
import pickle
from collections import deque
from typing import Tuple

import numpy as np
import tensorflow as tf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from utils.mediapipe_utils import normalize_landmarks


class SignLanguagePredictor:
    def __init__(
        self,
        model_path: str,
        encoder_path: str,
        smoothing_window: int = 7,
    ) -> None:
        self.model = tf.keras.models.load_model(model_path, compile=False)
        with open(encoder_path, "rb") as f:
            self.label_encoder = pickle.load(f)
        self.prob_window = deque(maxlen=smoothing_window)

    def reset(self) -> None:
        self.prob_window.clear()

    def _preprocess(self, landmarks: np.ndarray, handedness: str) -> np.ndarray:
        normalized = normalize_landmarks(landmarks, handedness)
        return normalized.flatten()[None, :]

    def predict(self, landmarks: np.ndarray, handedness: str) -> Tuple[str, float]:
        features = self._preprocess(landmarks, handedness)
        probs = self.model.predict(features, verbose=0)[0]
        self.prob_window.append(probs)
        avg_probs = np.mean(np.stack(self.prob_window, axis=0), axis=0)
        idx = int(np.argmax(avg_probs))
        label = self.label_encoder.inverse_transform([idx])[0]
        confidence = float(avg_probs[idx])
        return label, confidence
