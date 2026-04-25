import argparse
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import tensorflow as tf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)


def load_processed(path: str):
    data = np.load(path, allow_pickle=True)
    return data["X"], data["y"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ASL hand landmark classifier.")
    parser.add_argument("--data", type=str, default="data/processed/processed.npz")
    parser.add_argument("--model", type=str, default="models/asl_mlp.keras")
    parser.add_argument("--encoder", type=str, default="models/label_encoder.pkl")
    parser.add_argument("--splits", type=str, default="data/processed/splits.npz")
    parser.add_argument("--output-dir", type=str, default="data/processed")
    args = parser.parse_args()

    X, y = load_processed(args.data)

    with open(args.encoder, "rb") as f:
        label_encoder = pickle.load(f)

    y_encoded = label_encoder.transform(y)

    if os.path.exists(args.splits):
        splits = np.load(args.splits)
        test_idx = splits["test_idx"]
    else:
        test_idx = np.arange(len(X))

    X_test = X[test_idx]
    y_test = y_encoded[test_idx]

    model = tf.keras.models.load_model(args.model, compile=False)
    probs = model.predict(X_test, verbose=0)
    y_pred = np.argmax(probs, axis=1)

    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {acc:.4f}")

    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_)
    print("Classification report:")
    print(report)

    cm = confusion_matrix(y_test, y_pred)
    cm_df = pd.DataFrame(cm, index=label_encoder.classes_, columns=label_encoder.classes_)
    os.makedirs(args.output_dir, exist_ok=True)
    cm_path = os.path.join(args.output_dir, "confusion_matrix.csv")
    cm_df.to_csv(cm_path)

    print("Confusion matrix saved to:", cm_path)


if __name__ == "__main__":
    main()
