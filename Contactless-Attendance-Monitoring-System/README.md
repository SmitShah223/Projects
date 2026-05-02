# Contactless Attendance Monitoring System using Face Recognition

> **Published:** ICCDS February 2023 — ISBN: 979-8-9879839-0-4  
> **Authors:**  · Smit Shah · Darshit Shah · Parthav Shah  
> **Guide:** Mr. Sunil Khatri, Dept. of IoT, Thakur College of Engineering & Technology, Mumbai  
> **~95% recognition accuracy** | Raspberry Pi 4 | Python | OpenCV | dlib | SVM

---

## Overview

A fully contactless, automated attendance monitoring system built on **Raspberry Pi 4** using **face recognition** and **image processing**. The system is IR-triggered — it stays dormant until a person approaches, then activates the camera and performs face recognition in real time. Attendance is logged with timestamps, monthly reports are generated, and email alerts are sent for absent candidates.

Designed for schools, colleges, offices, and events. Built as a COVID-safe, hands-free alternative to fingerprint and RFID systems.

---

## Key Features

| Feature | Detail |
|---|---|
| Contactless | IR sensor triggers camera — no physical contact needed |
| Face recognition | dlib 128-D encodings + SVM classifier (~95% accuracy) |
| Multi-face | Detects and recognises multiple faces simultaneously |
| QR backup | 5-second-expiry QR code offered after 3 failed attempts |
| Monthly reports | CSV report: name, roll no, entry/exit time, percentage |
| Email alerts | Administrator email on absent candidates |
| OLED support | Optional visual confirmation on SSD1306 OLED display |
| Dormant when idle | IR sensor keeps Pi CPU usage near zero when no one present |

---

## System Architecture

```
                 KY-032 IR Sensor
                       │ GPIO 17
                       ▼
              ┌─────────────────┐
              │  Raspberry Pi 4  │◄─── 5MP CSI Camera
              │  (Linux / Python) │
              └────────┬─────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
    Face Recognition          Attendance Logger
    (dlib + SVM)              (CSV + email alert)
           │                       │
           ▼                       ▼
    Bounding box +           attendance.csv
    Name label on            monthly_report.csv
    live video stream
```

---

## Pipeline (from paper Fig. 4)

```
START
  │
  ▼
Initialize IR Sensor + Camera
  │
  ▼
IR Sensor Triggered? ── No ──► System stays dormant
  │ Yes
  ▼
Face Detection (Haar Cascade / HOG)
  │
  ▼
Face Recognition (dlib 128-D encoding → SVM)
  │
  ├── Face in database? ── Yes ──► Mark PRESENT in attendance DB
  │                                 Display name on video stream
  │                                 Send to OLED screen
  │
  └── Face NOT in database?
            │
            ├── Attempts < MAX ──► Show "Unknown" → try again
            └── Attempts ≥ MAX ──► Offer 5-second QR code backup
  │
  ▼
End of session:
  Mark remaining enrolled candidates as ABSENT
  Generate monthly report
  Send alert email to administrator
```

---

## Hardware

| Component | Model | Connection |
|---|---|---|
| Microcomputer | Raspberry Pi 4 (4GB) | — |
| Camera | 5MP CSI Camera Module | CSI ribbon port |
| IR Sensor | KY-032 Infrared Obstacle Avoidance | GPIO 17 (physical pin 11) |
| OLED (optional) | SSD1306 128×64 | I2C (SDA GPIO 2, SCL GPIO 3) |
| Power | 5V/3A USB-C | — |

### IR Sensor Wiring

| KY-032 | Raspberry Pi |
|---|---|
| VCC | 5V (pin 2) |
| GND | GND (pin 6) |
| OUT | GPIO 17 (physical pin 11) |

### Camera

Connect the 5MP CSI Camera Module to the Raspberry Pi's CSI camera port using the ribbon cable.  
Enable the camera with: `sudo raspi-config` → Interface Options → Camera → Enable.

---

## Repository Structure

```
Contactless-Attendance-Monitoring-System/
├── src/
│   ├── main.py                  # Main entry point — full pipeline
│   ├── config.py                # All configuration (paths, GPIO pins, thresholds)
│   ├── dataset/
│   │   └── capture.py           # Enroll new candidates (capture face images)
│   ├── trainer/
│   │   └── train.py             # Train dlib encodings + SVM classifier
│   ├── recognizer/
│   │   └── face_rec.py          # Real-time face recognition class
│   ├── attendance/
│   │   └── logger.py            # CSV attendance logger + monthly reports + email
│   └── utils/
│       ├── ir_sensor.py         # KY-032 IR sensor GPIO interface
│       └── qr_backup.py         # QR code backup attendance (5s expiry)
│
├── docs/
│   └── research_paper.pdf       # Published ICCDS 2023 paper
│
├── hardware/
│   └── circuit_diagram.png      # Raspberry Pi + IR sensor + camera wiring
│
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Set up Raspberry Pi

```bash
# Update OS
sudo apt update && sudo apt upgrade -y

# Install system dependencies (required for dlib/face_recognition)
sudo apt install -y build-essential cmake libatlas-base-dev \
    libopenblas-dev gfortran libhdf5-dev python3-dev python3-pip \
    python3-opencv libopencv-dev

# Enable camera
sudo raspi-config  # → Interface Options → Camera → Enable → Reboot
```

### 2. Install Python dependencies

```bash
cd Contactless-Attendance-Monitoring-System
pip3 install -r requirements.txt

# Note: face_recognition takes ~15 minutes to install on Pi (builds dlib from source)
# Consider using a pre-built wheel: https://github.com/ageitgey/face_recognition
```

### 3. Enroll candidates (capture dataset)

```bash
# Enroll each candidate — 75 frames captured automatically
python3 src/dataset/capture.py --id 21 --name "Darshit Shah"
python3 src/dataset/capture.py --id 22 --name "Parthav Shah"
python3 src/dataset/capture.py --id 23 --name "Smit Shah"
```

### 4. Train the model

```bash
# This encodes all faces and trains the SVM (~5–10 min on Pi for 3 candidates)
python3 src/trainer/train.py
```

### 5. Run the attendance system

```bash
# Normal mode — IR sensor triggers camera
python3 src/main.py --session-minutes 60

# Test mode — skip IR sensor (camera always on)
python3 src/main.py --no-ir --session-minutes 10

# With email alerts for absences
python3 src/main.py --admin-email admin@college.edu
```

---

## Attendance Output

### Live video stream

- **Green box + name** — candidate recognised, attendance marked ✅
- **Red box + "Unknown"** — face not in database ❌
- **QR window** — backup method after 3 failed attempts

### CSV files

**`src/attendance/attendance.csv`**
```
Date,CandidateID,Name,Status,EntryTime,ExitTime
2023-11-01,21,Darshit Shah,PRESENT,09:02:11,10:01:44
2023-11-01,22,Parthav Shah,PRESENT,09:03:55,10:01:44
2023-11-01,23,Smit Shah,ABSENT,,
```

**`src/attendance/report_2023_11.csv`** (monthly report)
```
CandidateID,Name,TotalDays,Present,Absent,Percentage
21,Darshit Shah,10,9,1,90.0%
22,Parthav Shah,10,10,0,100.0%
23,Smit Shah,10,8,2,80.0%
```

---

## Performance

| Metric | Value |
|---|---|
| Recognition accuracy | ~95% |
| Frames per second (Pi 4) | ~6–10 FPS |
| Encodings per face | 128 (fixed by dlib) |
| Frames per candidate | 75 (optimal per paper) |
| QR code validity | 5 seconds |

---

## Configuration

All settings in `src/config.py`:

```python
FRAMES_PER_CANDIDATE  = 75     # faces to capture per enrollment
IR_SENSOR_PIN         = 11     # physical GPIO pin for KY-032
MAX_FAILED_ATTEMPTS   = 3      # attempts before QR backup offered
QR_VALIDITY_SECONDS   = 5      # QR expires after this many seconds
MIN_CONFIDENCE        = 0.65   # SVM confidence threshold (0–1)
SESSION_TIMEOUT_MIN   = 60     # session duration in minutes
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `Cannot open camera` | Check CSI ribbon, enable camera in raspi-config |
| `face_recognition install fails` | Ensure cmake + libatlas installed; allow ~15min |
| `No face found in image` | Improve lighting; face must be ≥100×100px in frame |
| `GPIO permission denied` | Run with `sudo` or add user to `gpio` group |
| `OLED not displaying` | Check I2C address (0x3C or 0x3D); run `i2cdetect -y 1` |

---

## Citation

```
P. Shah, S. Shah, D. Shah, and S. Khatri, "Contactless Attendance Monitoring
System using Face Recognition and Image Processing," in Proc. International
Conference on Communication, Computing, and Data Security (ICCDS), Feb. 2023.
ISBN: 979-8-9879839-0-4.
```
