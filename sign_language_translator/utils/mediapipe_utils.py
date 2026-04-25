import numpy as np
import mediapipe as mp
from typing import Dict, List, Optional

HAND_LANDMARK_COUNT = 21
LANDMARK_DIMS = 3

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


def create_hands(
    static_image_mode: bool = False,
    max_num_hands: int = 2,
    min_detection_confidence: float = 0.6,
    min_tracking_confidence: float = 0.6,
) -> mp_hands.Hands:
    return mp_hands.Hands(
        static_image_mode=static_image_mode,
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def extract_hands(results) -> List[Dict]:
    hands: List[Dict] = []
    if not results:
        return hands

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks, results.multi_handedness
        ):
            coords = []
            for lm in hand_landmarks.landmark:
                coords.append([lm.x, lm.y, lm.z])

            handedness_label = handedness.classification[0].label
            handedness_score = float(handedness.classification[0].score)

            hands.append(
                {
                    "landmarks": np.array(coords, dtype=np.float32),
                    "handedness": handedness_label,
                    "score": handedness_score,
                    "raw": hand_landmarks,
                }
            )
    return hands


def select_primary_hand(hands: List[Dict]) -> Optional[Dict]:
    if not hands:
        return None
    return max(hands, key=lambda h: h.get("score", 0.0))


def normalize_landmarks(landmarks: np.ndarray, handedness: str) -> np.ndarray:
    if landmarks.shape != (HAND_LANDMARK_COUNT, LANDMARK_DIMS):
        raise ValueError(
            f"Expected landmarks shape {(HAND_LANDMARK_COUNT, LANDMARK_DIMS)}, got {landmarks.shape}"
        )

    normalized = landmarks.copy()

    if handedness.lower() == "left":
        normalized[:, 0] *= -1.0

    wrist = normalized[0]
    normalized = normalized - wrist

    scale = np.max(np.linalg.norm(normalized, axis=1))
    if scale < 1e-6:
        return np.zeros_like(normalized, dtype=np.float32)

    normalized = normalized / scale
    return normalized.astype(np.float32)


def landmarks_to_feature(landmarks: np.ndarray, handedness: str) -> np.ndarray:
    normalized = normalize_landmarks(landmarks, handedness)
    return normalized.flatten()


def draw_hand_landmarks(image, hand_landmarks) -> None:
    mp_drawing.draw_landmarks(
        image,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing_styles.get_default_hand_landmarks_style(),
        mp_drawing_styles.get_default_hand_connections_style(),
    )
