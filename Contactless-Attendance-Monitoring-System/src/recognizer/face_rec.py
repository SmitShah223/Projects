"""
recognizer/face_rec.py — Real-time face recognition using the trained SVM model.

Pipeline (matches paper Section II-D, II-E):
  1. Read frame from camera
  2. Detect faces using HOG (dlib) or Haar Cascade (OpenCV)
  3. Compute 128-D face encoding for each detected face
  4. Predict candidate identity using SVM
  5. If confidence >= threshold → recognized; else → "Unknown"
  6. Return list of (name, candidate_id, confidence, bounding_box)
"""

import os
import sys
import pickle
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SVM_MODEL_PATH, RECOGNITION_TOLERANCE, MIN_CONFIDENCE,
    HAAR_CASCADE_PATH, CAMERA_RESOLUTION
)

try:
    import face_recognition
except ImportError:
    raise ImportError("Run: pip3 install face_recognition")


class FaceRecognizer:
    """
    Loads trained SVM model and performs real-time face recognition on frames.
    """

    def __init__(self):
        if not os.path.exists(SVM_MODEL_PATH):
            raise FileNotFoundError(
                f"No trained model found at {SVM_MODEL_PATH}. "
                "Run src/trainer/train.py first."
            )
        with open(SVM_MODEL_PATH, "rb") as f:
            data = pickle.load(f)

        self.clf          = data["classifier"]
        self.le           = data["label_encoder"]
        self.label_names  = data["label_names"]

        # Haar cascade as a lightweight fallback detector
        self.haar = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

        print(f"[FaceRec] Model loaded. {len(self.label_names)} candidates enrolled.")

    def predict_frame(self, frame_bgr):
        """
        Detect and recognise faces in a single BGR frame.

        Args:
            frame_bgr: OpenCV BGR frame from camera

        Returns:
            results: list of dicts:
                {
                  "name":        str   — candidate name or "Unknown"
                  "id":          str   — candidate ID or None
                  "confidence":  float — SVM probability (0–1)
                  "box":         (top, right, bottom, left) — face bounding box
                }
            annotated_frame: frame with bounding boxes and labels drawn
        """
        # Convert BGR → RGB for face_recognition library
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Detect face locations (HOG, fast on Raspberry Pi 4)
        face_locations = face_recognition.face_locations(rgb, model="hog",
                                                          number_of_times_to_upsample=1)

        if not face_locations:
            return [], frame_bgr

        # Compute 128-D encodings
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        results = []
        annotated = frame_bgr.copy()

        for enc, (top, right, bottom, left) in zip(face_encodings, face_locations):
            name        = "Unknown"
            candidate_id = None
            confidence   = 0.0

            # SVM prediction
            enc_arr = np.array([enc])
            proba   = self.clf.predict_proba(enc_arr)[0]
            best_idx = np.argmax(proba)
            conf     = proba[best_idx]

            if conf >= MIN_CONFIDENCE:
                label_id     = self.le.inverse_transform([best_idx])[0]
                name         = self.label_names.get(label_id, f"ID_{label_id}")
                candidate_id = label_id
                confidence   = float(conf)

            results.append({
                "name":       name,
                "id":         candidate_id,
                "confidence": confidence,
                "box":        (top, right, bottom, left),
            })

            # ── Annotate frame ─────────────────────────────────────────────
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            label = f"{name} ({conf:.0%})" if name != "Unknown" else "Unknown"
            cv2.rectangle(annotated, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
            cv2.putText(annotated, label, (left + 4, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        return results, annotated

    def get_enrolled_ids(self):
        """Return set of all enrolled candidate IDs."""
        return set(self.label_names.keys())
