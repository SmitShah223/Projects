"""
trainer/train.py — Train the face recognition model.

Pipeline (matches paper Section II-B & II-E):
  1. Load all face images from dataset/
  2. Use dlib (via face_recognition) to generate 128-D face encodings
  3. Train an SVM classifier (Scikit-Learn) on these encodings
  4. Serialize the SVM model and encodings to disk

The SVM creates a face recognition model that works with minimal
latency on the Raspberry Pi 4.

Usage:
    python3 src/trainer/train.py

Dependencies:
    face_recognition  scikit-learn  numpy  Pillow
    sudo apt install libatlas-base-dev libopenblas-dev  (Raspberry Pi)
    pip3 install face_recognition scikit-learn numpy Pillow
"""

import os
import sys
import pickle
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATASET_DIR, SVM_MODEL_PATH, ENCODINGS_PATH, DLIB_FACE_ENCODINGS

try:
    import face_recognition
    from sklearn.svm import SVC
    from sklearn.preprocessing import LabelEncoder
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    print(f"[TRAIN] Missing dependency: {e}")
    print("[TRAIN] Run: pip3 install face_recognition scikit-learn")
    sys.exit(1)


def load_images_from_dataset(dataset_dir: str):
    """
    Walk the dataset directory and load all face images.

    Returns:
        images     : list of numpy arrays (RGB)
        labels     : list of candidate IDs (str)
        label_names: dict mapping ID → full name
    """
    images, labels, label_names = [], [], {}

    for candidate_folder in sorted(os.listdir(dataset_dir)):
        folder_path = os.path.join(dataset_dir, candidate_folder)
        if not os.path.isdir(folder_path):
            continue

        # Folder name format: "23_Smit_Shah"
        parts = candidate_folder.split("_", 1)
        candidate_id   = parts[0]
        candidate_name = parts[1].replace("_", " ") if len(parts) > 1 else candidate_id
        label_names[candidate_id] = candidate_name

        for img_file in sorted(os.listdir(folder_path)):
            if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img_path = os.path.join(folder_path, img_file)
            try:
                img = Image.open(img_path).convert("RGB")
                images.append(np.array(img))
                labels.append(candidate_id)
            except Exception as ex:
                print(f"[TRAIN] Warning: could not load {img_path}: {ex}")

    return images, labels, label_names


def compute_encodings(images):
    """
    Generate 128-D face encodings using dlib (via face_recognition).
    Skips images where no face is detected.
    Returns list of (encoding, original_index) tuples.
    """
    encodings = []
    valid_indices = []

    for i, img in enumerate(images):
        # Detect face locations using HOG (default, fast on Pi 4)
        face_locations = face_recognition.face_locations(img, model="hog",
                                                          number_of_times_to_upsample=1)
        if not face_locations:
            print(f"[TRAIN] Warning: no face found in image {i} — skipping")
            continue

        # Generate 128-D encoding for first detected face
        enc = face_recognition.face_encodings(img, known_face_locations=face_locations)
        if enc:
            encodings.append(enc[0])
            valid_indices.append(i)

    return encodings, valid_indices


def train():
    print("[TRAIN] Loading images from dataset...")
    images, labels, label_names = load_images_from_dataset(DATASET_DIR)

    if not images:
        print(f"[TRAIN] No images found in {DATASET_DIR}.")
        print("[TRAIN] Run dataset/capture.py first to enroll candidates.")
        return

    print(f"[TRAIN] Loaded {len(images)} images across {len(label_names)} candidates.")
    print("[TRAIN] Computing 128-D face encodings (this may take a few minutes on Pi)...")

    encodings, valid_indices = compute_encodings(images)
    valid_labels = [labels[i] for i in valid_indices]

    print(f"[TRAIN] Encoded {len(encodings)}/{len(images)} images successfully.")

    # ── Encode labels ─────────────────────────────────────────────────────────
    le = LabelEncoder()
    y  = le.fit_transform(valid_labels)

    X  = np.array(encodings)

    # ── Train SVM ─────────────────────────────────────────────────────────────
    print("[TRAIN] Training SVM classifier...")
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10.0, gamma="scale",
                       probability=True, random_state=42)),
    ])
    clf.fit(X, y)
    print("[TRAIN] SVM training complete.")

    # ── Save model + encodings ────────────────────────────────────────────────
    model_data = {
        "classifier":  clf,
        "label_encoder": le,
        "label_names": label_names,
    }
    with open(SVM_MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)
    print(f"[TRAIN] ✅ SVM model saved to {SVM_MODEL_PATH}")

    # Also save raw encodings for future use / re-training
    enc_data = {
        "encodings": encodings,
        "labels":    valid_labels,
        "label_names": label_names,
    }
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(enc_data, f)
    print(f"[TRAIN] ✅ Encodings saved to {ENCODINGS_PATH}")


if __name__ == "__main__":
    train()
