# Real-time ASL Sign Language Translator

A modular, production-ready pipeline that collects hand landmark data with MediaPipe, trains a TensorFlow model on ASL alphabet gestures (A–Z), and performs real-time translation from a live webcam feed into text (with optional speech).

## Tech Stack
- Python 3.10
- OpenCV >= 4.8
- MediaPipe 0.10.x (Hands)
- TensorFlow >= 2.13 (TF only)
- NumPy, Pandas, Scikit-learn
- Optional: `pyttsx3` for offline text-to-speech

## Project Structure
```
sign_language_translator/
├── data/
│   ├── raw/
│   ├── processed/
│   └── labels.csv
├── data_collection/
│   └── collect_data.py
├── preprocessing/
│   └── preprocess.py
├── training/
│   ├── model.py
│   ├── train_model.py
│   └── evaluate.py
├── inference/
│   └── predictor.py
├── realtime/
│   └── realtime_translator.py
├── utils/
│   ├── mediapipe_utils.py
│   └── visualization.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup
From the repository root:
```
cd sign_language_translator
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 1) Data Collection
Collect labeled hand landmarks from your webcam. Press `A`–`Z` to save the current hand pose, `Q` to quit.

```
python data_collection/collect_data.py --camera 0
```

Outputs raw CSV files to `data/raw/`.

## 2) Preprocessing
Normalize landmarks for translation/scale invariance and build fixed-length feature vectors.

```
python preprocessing/preprocess.py --raw-dir data/raw --output-dir data/processed
```

Outputs:
- `data/processed/processed.npz` (X, y)
- `data/processed/processed.csv`

## 3) Training
Train a compact MLP classifier on the processed landmarks.

```
python training/train_model.py --data data/processed/processed.npz
```

Saved artifacts:
- `models/asl_mlp.keras`
- `models/label_encoder.pkl`
- `data/processed/splits.npz`

## 4) Evaluation
Evaluate model accuracy and generate a confusion matrix.

```
python training/evaluate.py --data data/processed/processed.npz
```

Outputs:
- Accuracy + classification report in console
- `data/processed/confusion_matrix.csv`

## 5) Real-time Translation
Run the real-time translator on your webcam. Toggle TTS with `T`, quit with `Q` or `Esc`.

```
python realtime/realtime_translator.py --camera 0 --tts
```

## Notes on Extensibility
- The pipeline already handles modular data collection, preprocessing, training, and inference.
- Extending to words/sentences can be done by adding a temporal model (e.g., LSTM/TCN) and logging sequences over time.
- `utils/mediapipe_utils.py` centralizes landmark normalization and can be reused for new datasets or model types.

## Troubleshooting
- If no hand is detected, ensure good lighting and keep your hand within the camera frame.
- If TTS is enabled but silent, verify `pyttsx3` is installed and working on your OS.
- For performance, close other camera-using applications and reduce webcam resolution if needed.
