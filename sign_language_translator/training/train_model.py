import argparse
import os
import pickle
import sys
from typing import Tuple

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from training.model import build_mlp


def load_processed(path: str) -> Tuple[np.ndarray, np.ndarray]:
    data = np.load(path, allow_pickle=True)
    return data["X"], data["y"]


def create_splits(X: np.ndarray, y: np.ndarray, seed: int = 42):
    indices = np.arange(len(X))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.15, stratify=y, random_state=seed
    )
    train_idx, val_idx = train_test_split(
        train_idx,
        test_size=0.1765,
        stratify=y[train_idx],
        random_state=seed,
    )
    return train_idx, val_idx, test_idx


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ASL hand landmark classifier.")
    parser.add_argument("--data", type=str, default="data/processed/processed.npz")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--model-out", type=str, default="models/asl_mlp.keras")
    parser.add_argument("--encoder-out", type=str, default="models/label_encoder.pkl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--splits-out", type=str, default="data/processed/splits.npz")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.model_out), exist_ok=True)
    os.makedirs(os.path.dirname(args.encoder_out), exist_ok=True)
    os.makedirs(os.path.dirname(args.splits_out), exist_ok=True)

    tf.random.set_seed(args.seed)
    np.random.seed(args.seed)

    X, y = load_processed(args.data)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    train_idx, val_idx, test_idx = create_splits(X, y_encoded, seed=args.seed)
    np.savez_compressed(
        args.splits_out, train_idx=train_idx, val_idx=val_idx, test_idx=test_idx
    )

    X_train, y_train = X[train_idx], y_encoded[train_idx]
    X_val, y_val = X[val_idx], y_encoded[val_idx]

    num_classes = len(label_encoder.classes_)

    y_train_cat = tf.keras.utils.to_categorical(y_train, num_classes=num_classes)
    y_val_cat = tf.keras.utils.to_categorical(y_val, num_classes=num_classes)

    model = build_mlp(input_dim=X.shape[1], num_classes=num_classes)

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            args.model_out,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=10,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_accuracy",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    history = model.fit(
        X_train,
        y_train_cat,
        validation_data=(X_val, y_val_cat),
        epochs=args.epochs,
        batch_size=args.batch_size,
        verbose=1,
    )

    with open(args.encoder_out, "wb") as f:
        pickle.dump(label_encoder, f)

    # Always save a final model snapshot in case checkpoint never triggers
    model.save(args.model_out)

    print("Training complete.")
    print(f"Best model saved to: {args.model_out}")
    print(f"Label encoder saved to: {args.encoder_out}")

    return history


if __name__ == "__main__":
    main()
