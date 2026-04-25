Real-time ASL Sign Language Translator - Step-by-Step Guide

This guide walks you through the full project: data collection, preprocessing, training, evaluation, and real-time inference.

1) Prerequisites
- Python 3.10 installed
- A working webcam
- Internet access for installing dependencies

2) Create and activate a virtual environment (recommended)
- From the project root:
  - macOS/Linux:
    python3.10 -m venv .venv
    source .venv/bin/activate
  - Windows (PowerShell):
    python3.10 -m venv .venv
    .venv\Scripts\Activate.ps1

3) Install dependencies
- From the project root:
  pip install -r requirements.txt

4) Collect data (A–Z)
- Run the data collector:
  python data_collection/collect_data.py --camera 0
- Instructions while collecting:
  - Press keys A–Z to save the current hand pose with that label.
  - Press Q or Esc to quit.
- Output files will be saved in:
  data/raw/

5) Preprocess raw data
- Run preprocessing to normalize and build feature vectors:
  python preprocessing/preprocess.py --raw-dir data/raw --output-dir data/processed
- Outputs:
  data/processed/processed.npz
  data/processed/processed.csv

6) Train the model
- Train the MLP classifier:
  python training/train_model.py --data data/processed/processed.npz
- Outputs:
  models/asl_mlp.keras
  models/label_encoder.pkl
  data/processed/splits.npz

7) Evaluate the model
- Evaluate and generate a confusion matrix:
  python training/evaluate.py --data data/processed/processed.npz
- Outputs:
  Accuracy + classification report in console
  data/processed/confusion_matrix.csv

8) Run real-time translator
- Start the webcam translator:
  python realtime/realtime_translator.py --camera 0 --tts
- Controls:
  - Press T to toggle text-to-speech
  - Press Q or Esc to quit

9) Optional: Use the unified main entry point
- You can also run each stage via main.py:
  python main.py collect
  python main.py preprocess
  python main.py train
  python main.py evaluate
  python main.py realtime

10) Extending to words/sentences (overview)
- Collect sequences over time instead of single frames
- Replace the MLP with a temporal model (LSTM/GRU/TCN)
- Keep the same preprocessing normalization for each frame
- python realtime/realtime_translator_sentences.py --camera 0 --tts --speak-mode sentence

Troubleshooting
- If no hand is detected, ensure good lighting and center your hand in the frame.
- If TTS is silent, confirm pyttsx3 works on your OS and audio output is enabled.
- For better accuracy, collect balanced samples for each letter.
