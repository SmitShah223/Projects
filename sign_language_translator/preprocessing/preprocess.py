import argparse
import glob
import os
import sys
from typing import Tuple

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from utils.mediapipe_utils import normalize_landmarks


LANDMARK_COLS = [
    f"lm{i}_{axis}" for i in range(21) for axis in ("x", "y", "z")
]


def load_raw_data(raw_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    frames = []
    skipped = []

    for f in files:
        try:
            if os.path.getsize(f) == 0:
                skipped.append((f, "empty file"))
                continue
        except OSError:
            skipped.append((f, "unreadable file"))
            continue

        try:
            df = pd.read_csv(f)
        except pd.errors.EmptyDataError:
            skipped.append((f, "no columns"))
            continue

        if df.empty:
            skipped.append((f, "no rows"))
            continue

        frames.append(df)

    if not frames:
        details = ", ".join([f"{os.path.basename(f)}:{reason}" for f, reason in skipped])
        if not details:
            details = "none"
        raise ValueError(f"No valid CSV data found in {raw_dir}. Skipped files: {details}")

    data = pd.concat(frames, ignore_index=True)
    missing_cols = [c for c in ["label", "handedness"] + LANDMARK_COLS if c not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in raw data: {missing_cols}")

    if skipped:
        details = ", ".join([f"{os.path.basename(f)}:{reason}" for f, reason in skipped])
        print(f"Warning: skipped {len(skipped)} file(s): {details}")

    return data


def preprocess_data(data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    labels = data["label"].astype(str).values
    handedness = data["handedness"].fillna("Right").astype(str).values

    X = np.zeros((len(data), 63), dtype=np.float32)

    for idx, row in data.iterrows():
        landmarks = row[LANDMARK_COLS].values.astype(np.float32).reshape(21, 3)
        normalized = normalize_landmarks(landmarks, handedness[idx])
        X[idx] = normalized.flatten()

    return X, labels


def save_processed(
    X: np.ndarray,
    y: np.ndarray,
    output_dir: str,
    output_name: str,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    npz_path = os.path.join(output_dir, f"{output_name}.npz")
    np.savez_compressed(npz_path, X=X, y=y)

    csv_path = os.path.join(output_dir, f"{output_name}.csv")
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
    df.insert(0, "label", y)
    df.to_csv(csv_path, index=False)

    print(f"Saved processed data to {npz_path} and {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess raw ASL hand landmark data.")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory with raw CSV files")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory for processed data")
    parser.add_argument("--output-name", type=str, default="processed", help="Base filename for processed data")
    args = parser.parse_args()

    data = load_raw_data(args.raw_dir)
    X, y = preprocess_data(data)
    save_processed(X, y, args.output_dir, args.output_name)


if __name__ == "__main__":
    main()
