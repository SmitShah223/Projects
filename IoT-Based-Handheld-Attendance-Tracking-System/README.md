# IoT-Based Handheld Attendance Tracking System

> **Published:** ICCDS February 2024 — ISBN: 979-8-9879839-7-3  
> **Authors:** Darshit Shah · Parthav Shah · Smit Shah  
> **Guide:** Mr. Sunil Khatri, Dept. of IoT, Thakur College of Engineering & Technology, Mumbai

---

## Overview

A portable, dual-authentication attendance tracking system that combines **RFID** and **biometric fingerprint** recognition to automate student attendance in educational institutions. Attendance records are stored locally on the device (offline-capable) and synced to **AWS IoT Core → RDS MySQL** in real time when Wi-Fi is available.

### Key Features

| Feature | Detail |
|---|---|
| Dual authentication | RFID card (RC522) + fingerprint (R307) — both must pass |
| Portable | Runs on Li-ion battery, no wall power needed |
| Offline capable | Local SPIFFS storage; syncs to cloud when online |
| Cloud backend | AWS EC2 (FastAPI) + AWS RDS (MySQL) + AWS IoT Core (MQTT/TLS) |
| Real-time analytics | Attendance percentage, per-day records, trends |
| Security | TLS-encrypted MQTT; admin-only cloud write access |

---

## System Architecture

```
┌──────────────────────────────────┐
│         ESP32 DevKit             │
│  ┌──────────┐  ┌──────────────┐  │
│  │  RC522   │  │  R307 FP     │  │
│  │  RFID    │  │  Sensor      │  │
│  └────┬─────┘  └──────┬───────┘  │
│       │ SPI           │ UART2    │
│       └───────┬────────┘         │
│          ESP32 MCU               │
│     (SPIFFS local storage)       │
└──────────────┬───────────────────┘
               │ MQTT over TLS (port 8883)
               ▼
     ┌──────────────────┐
     │  AWS IoT Core    │
     └────────┬─────────┘
              │
    ┌─────────┴──────────┐
    │   AWS EC2           │
    │   FastAPI Server    │
    │   (MQTT listener)   │
    └─────────┬───────────┘
              │ SQLAlchemy
              ▼
     ┌──────────────────┐
     │   AWS RDS MySQL  │
     │   attendance_db  │
     └──────────────────┘
```

---

## Hardware Components

| Component | Model | Interface |
|---|---|---|
| Microcontroller | ESP32 DevKit V1 | — |
| RFID Reader | MFRC522 (RC522) | SPI |
| Fingerprint Sensor | R307 | UART (57600 baud) |
| Battery | Li-ion 3.7V | — |
| Charging Module | TP4056 | — |
| LEDs (×4) | Green / Yellow / Blue / Red | GPIO |

### Wiring Summary

**RC522 → ESP32:**
| RC522 | ESP32 |
|---|---|
| SDA | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| RST | GPIO 0 |
| 3.3V | 3.3V |
| GND | GND |

**R307 → ESP32:**
| R307 | ESP32 |
|---|---|
| TX (green) | GPIO 16 (RX2) |
| RX (white) | GPIO 17 (TX2) |
| VCC (red) | 3.3–5V |
| GND (black) | GND |

---

## Repository Structure

```
IoT-Based-Handheld-Attendance-Tracking-System/
├── firmware/
│   ├── main/
│   │   ├── main.ino            # Main Arduino sketch
│   │   └── secrets.h           # AWS credentials (NOT committed)
│   └── lib/
│       ├── rfid_handler/       # RC522 RFID driver
│       ├── fingerprint_handler/ # R307 fingerprint driver
│       ├── wifi_mqtt/          # Wi-Fi + AWS IoT Core MQTT
│       ├── local_storage/      # SPIFFS offline storage
│       └── led_feedback/       # LED status indicator
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── api/
│   │   │   ├── attendance.py   # Attendance endpoints
│   │   │   └── students.py     # Student CRUD endpoints
│   │   ├── db/
│   │   │   ├── models.py       # SQLAlchemy ORM models
│   │   │   ├── schemas.py      # Pydantic schemas
│   │   │   └── database.py     # DB session factory
│   │   ├── dependencies/
│   │   │   ├── authentication.py
│   │   │   └── mqtt.py         # AWS IoT Core MQTT listener
│   │   └── config/
│   │       └── settings.py     # Environment config
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   └── project_report.pdf      # Full semester report
│
├── hardware/
│   └── circuit_diagram.png     # Breadboard layout
│
├── .gitignore
└── README.md
```

---

## Quick Start

### Firmware (ESP32)

1. Install [Arduino IDE](https://www.arduino.cc/en/software) + ESP32 board support
2. Install libraries via Library Manager:
   - `MFRC522` by miguelbalboa
   - `Adafruit Fingerprint Sensor Library`
   - `PubSubClient` by Nick O'Leary
   - `ArduinoJson` by Benoit Blanchon
3. Copy `firmware/main/secrets.h` template and fill in your AWS + Wi-Fi credentials
4. Open `firmware/main/main.ino` in Arduino IDE
5. Select board: **ESP32 Dev Module** → Upload

### Backend (FastAPI on AWS EC2)

```bash
# Clone repo, navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in DB credentials, AWS IoT endpoint, admin password

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs available at `http://<ec2-ip>:8000/docs`

---

## Attendance Flow

```
Student presents RFID card
        │
        ▼
  RC522 reads UID ──── not in cache ──▶ Reject (red LED ×3)
        │
      in cache
        │
        ▼
  Prompt fingerprint (blue LED)
        │
        ▼
  R307 scans finger ── mismatch ──▶ Reject (red LED ×3)
        │
      match
        │
        ▼
  Log to SPIFFS (offline safe)
        │
        ▼
  Wi-Fi available? ── No ──▶ Queue for later sync
        │ Yes
        ▼
  Publish to AWS IoT Core (MQTT/TLS)
        │
        ▼
  Server validates → writes AttendanceLog → ACKs device
        │
        ▼
  Green LED ×2 ✅
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server health check |
| GET | `/students/` | List all students (admin) |
| POST | `/students/` | Register new student (admin) |
| POST | `/students/register-device` | Push student UID to devices via MQTT |
| GET | `/attendance/` | List all attendance records (admin) |
| GET | `/attendance/student/{id}` | Records for one student |
| GET | `/attendance/analytics` | Summary statistics for dashboard |

---

## Security

- MQTT communication is TLS-encrypted (port 8883)
- AWS IoT Core certificates are per-device (never shared)
- `secrets.h` and `.env` are gitignored — never committed
- Admin endpoints protected by HTTP Basic Auth

---

## Citation

If you use this project in your research, please cite:

```
D. Shah, P. Shah, S. Shah, and S. Khatri, "IoT-Based Handheld Attendance
Tracking System with Real-time Data Visualization and Analysis," in Proc.
International Conference on Communication, Computing, and Data Security
(ICCDS), Feb. 2024. ISBN: 979-8-9879839-7-3.
```
