"""
config.py — Central configuration for the Contactless Attendance System.

Hardware:
    Raspberry Pi 4 (4GB RAM, 1.5GHz quad-core)
    5MP CSI Camera Module
    KY-032 IR Obstacle Avoidance Sensor

Published: ICCDS February 2023 (ISBN: 979-8-9879839-0-4)
Authors:   Darshit Shah, Parthav Shah, Smit Shah
Guide:     Mr. Sunil Khatri, Dept. of IoT, TCET Mumbai
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR    = os.path.join(BASE_DIR, "src", "dataset")   # raw face images
TRAINER_DIR    = os.path.join(BASE_DIR, "src", "trainer")   # trained model
ATTENDANCE_DIR = os.path.join(BASE_DIR, "src", "attendance") # CSV logs

os.makedirs(DATASET_DIR,    exist_ok=True)
os.makedirs(TRAINER_DIR,    exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# ─── Dataset capture settings ─────────────────────────────────────────────────
FRAMES_PER_CANDIDATE = 75     # 64–86 per paper; 75 is optimal
CAPTURE_DELAY_MS     = 100    # ms between captured frames

# ─── Face detection ───────────────────────────────────────────────────────────
HAAR_CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
HOG_UPSAMPLES     = 1         # number of HOG upsamples for dlib detector

# ─── SVM / face recognition ───────────────────────────────────────────────────
DLIB_FACE_ENCODINGS = 128     # data points per face (fixed by dlib)
SVM_MODEL_PATH      = os.path.join(TRAINER_DIR, "svm_model.pkl")
ENCODINGS_PATH      = os.path.join(TRAINER_DIR, "encodings.pkl")
RECOGNITION_TOLERANCE = 0.5  # lower = stricter match (0.4–0.6 typical)
MIN_CONFIDENCE      = 0.65   # SVM confidence threshold for valid prediction

# ─── IR Sensor (GPIO) ─────────────────────────────────────────────────────────
IR_SENSOR_PIN = 11            # BCM GPIO 17 → physical pin 11

# ─── QR Code backup ───────────────────────────────────────────────────────────
QR_VALIDITY_SECONDS  = 5     # QR code expires after 5s to prevent proxy
MAX_FAILED_ATTEMPTS  = 3     # failed face-rec attempts before QR is offered

# ─── Attendance ───────────────────────────────────────────────────────────────
ATTENDANCE_CSV       = os.path.join(ATTENDANCE_DIR, "attendance.csv")
SESSION_TIMEOUT_MIN  = 60    # mark all unrecognised as absent after this many minutes

# ─── Camera ───────────────────────────────────────────────────────────────────
CAMERA_RESOLUTION    = (640, 480)
CAMERA_FRAMERATE     = 30
DISPLAY_WINDOW_NAME  = "Frame"
