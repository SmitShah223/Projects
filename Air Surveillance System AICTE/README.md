# Helium Balloon-Based IoT Aerial Surveillance System

> **Project:** AICTE Air Surveillance System  
> **Institution:** Thakur College of Engineering & Technology, Mumbai  
> **Hardware:** ESP32-CAM · SIM800L GPRS · LiPo Battery · Buck Converter · 3D-Printed Enclosure · Helium Balloon  
> **Protocol:** GPRS → HTTP POST → Cloud Server (no Wi-Fi required)

---

## Overview

A self-contained aerial surveillance payload mounted on a helium balloon. The **ESP32-CAM** captures JPEG images and uploads them to a cloud server via a **SIM800L GSM/GPRS module** — no Wi-Fi, no drone, no complex regulations. The system runs on a **LiPo battery** regulated to 5V by a buck converter, and enters **deep sleep** between capture cycles to maximise battery life.

Built as a low-cost, easily-deployable alternative to satellites and drones for stationary area monitoring (lake observation, event coverage, environmental sensing).

---

## System Architecture

```
┌──────────────────────────────────────────┐
│           3D-Printed Enclosure           │
│  ┌────────────────────────────────────┐  │
│  │        ESP32-CAM (AI-Thinker)      │  │
│  │   OV2640 2MP · 4MB PSRAM           │  │
│  └──────┬──────────────┬──────────────┘  │
│         │ SoftSerial   │ Camera I2S      │
│  ┌──────▼──────┐  ┌────▼─────┐          │
│  │  SIM800L    │  │ OV2640   │          │
│  │  GPRS Quad  │  │ 70° FOV  │──► lens  │
│  │  band GSM   │  └──────────┘   aperture│
│  └──────┬──────┘                         │
│         │ GSM antenna port              │
│  ┌──────▼──────┐                        │
│  │ LiPo 3.7V  │──► Buck Conv ──► 5V    │
│  └─────────────┘                        │
└──────────────────────────────────────────┘
            │ tether / string
      ┌─────▼─────┐
      │  HELIUM   │
      │  BALLOON  │
      └───────────┘
```

---

## Operational Flow

```
POWER ON (or wake from deep sleep)
        │
        ▼
1. Initialise camera (OV2640 + PSRAM)
        │
        ▼
2. Register on GSM network + open GPRS bearer
        │
        ▼
3. Camera warm-up (3 frames) → capture JPEG
        │
        ▼
4. Buffer JPEG in PSRAM (up to 4MB)
        │
        ▼
5. HTTP POST JPEG to cloud server via SIM800L
   [AT+HTTPINIT → AT+HTTPPARA → AT+HTTPDATA → AT+HTTPACTION=1]
        │
        ▼
6. Image available on cloud server for remote viewing
        │
        ▼
7. Close GPRS bearer → enter deep sleep (60s)
   (10µA sleep vs 160mA active)
        │
        └──► Wake → restart from step 1
```

---

## Hardware Components

| Component | Model / Spec | Role |
|---|---|---|
| Microcontroller | ESP32-CAM AI-Thinker | Main controller + image processor |
| Camera | OV2640 2MP, 70° FOV | Image capture (integrated on ESP32-CAM) |
| GSM/GPRS Module | SIM800L Quad-band | Cellular data upload |
| Battery | LiPo 3.7V ~370mAh | Portable power source |
| Voltage Regulator | Buck converter (5V out) | Steps 3.7V → stable 5V |
| Enclosure | 3D-printed PLA/ABS | Protection + mounting |
| Platform | Helium balloon | Aerial lift |

---

## Pin Map (ESP32-CAM AI-Thinker)

| Signal | ESP32-CAM Pin | Connected To |
|---|---|---|
| SIM800L RX | GPIO 14 | SIM800L TX |
| SIM800L TX | GPIO 15 | SIM800L RX |
| Battery ADC | GPIO 33 | Voltage divider (100kΩ/100kΩ) |
| Status LED | GPIO 33 (onboard) | Built-in red LED |
| Flash LED | GPIO 4 | Built-in flash LED |
| Camera pins | GPIO 0,25–27,34–36,39 | OV2640 (internal) |

> **⚠️ GPIO 0:** Must be HIGH on boot. Pulled LOW for flashing mode. Do not ground during normal operation.

---

## Repository Structure

```
Air Surveillance System AICTE/
├── src/
│   ├── main/
│   │   └── main.ino               # Full operational flow (init→capture→upload→sleep)
│   └── lib/
│       ├── config/
│       │   └── config.h            # All settings: APN, server URL, sleep interval
│       ├── camera/
│       │   ├── camera.h            # OV2640 camera interface
│       │   └── camera.cpp          # AI-Thinker pin mapping + capture logic
│       ├── gsm_gprs/
│       │   ├── gsm_gprs.h          # SIM800L interface
│       │   └── gsm_gprs.cpp        # AT command driver: GPRS connect + HTTP POST
│       └── power_manager/
│           ├── power_manager.h     # Deep sleep + battery voltage interface
│           └── power_manager.cpp   # esp_deep_sleep + ADC battery reading
│
├── docs/
│   └── helium-balloon-iot-surveillance-system.pdf
│
├── media/
│   ├── encasing.jpg               # 3D-printed enclosure photo
│   └── 3d-print.jpeg              # 3D print design
│
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Board Setup (Arduino IDE)

- Install: **esp32 by Espressif Systems** via Board Manager
- Select board: **AI Thinker ESP32-CAM**
- Upload speed: **115200**
- Flash mode: **QIO**

### 2. Configure `src/lib/config/config.h`

```cpp
// Your SIM card's APN (find from carrier)
#define GSM_APN      "airtelgprs.com"   // e.g. "jionet", "bsnlnet"

// Your cloud server endpoint
#define SERVER_HOST  "your-server.example.com"
#define SERVER_PORT  80
#define SERVER_PATH  "/upload"

// Capture every 60 seconds
#define CAPTURE_INTERVAL_S  60
```

### 3. Set Up Cloud Server

A minimal Python Flask server to receive images:

```python
from flask import Flask, request
import os, datetime

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_data()
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(UPLOAD_DIR, f"balloon_{ts}.jpg")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Received {len(data)} bytes → {path}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
```

### 4. Flash ESP32-CAM

The ESP32-CAM has no onboard USB-UART. Use an FTDI adapter:
```
FTDI TX  → ESP32-CAM GPIO 3 (U0RX)
FTDI RX  → ESP32-CAM GPIO 1 (U0TX)
FTDI GND → ESP32-CAM GND
FTDI 5V  → ESP32-CAM 5V

For flash mode: GPIO 0 → GND (hold during power-on, release after upload starts)
```

### 5. Deploy

1. Insert SIM card (GPRS-enabled, data plan active)
2. Power on → observe Serial Monitor for status
3. Attach to 3D-printed enclosure
4. Mount on helium balloon tether
5. Images upload to cloud every 60 seconds

---

## Deep Sleep Power Budget

| State | Current | Duration |
|---|---|---|
| Active (capture + upload) | ~160mA | ~15–20s per cycle |
| Deep sleep | ~10µA | ~40s per cycle |
| Average (60s cycle) | ~45mA | — |
| Battery life (~370mAh) | **~8 hours** | — |

To extend: increase `CAPTURE_INTERVAL_S`, or add solar panel charging (future scope).

---

## Future Scope (from project document)

- **GPS tagging** — NEO-6M module to geotag each image with precise coordinates
- **Solar charging** — lightweight flexible panels on casing exterior for continuous operation
- **On-demand capture** — remote SMS command to trigger capture
- **Sensor fusion** — temperature, humidity, air quality alongside visual data
- **Higher altitude** — larger weather balloon for heavier payload + greater stability

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Camera init fails | Check 5V supply; GPIO 0 must be HIGH on boot |
| GSM no response | Verify SIM800L power (needs ~500mA–2A; use buck converter) |
| GPRS connect fails | Check APN string for your carrier; ensure data plan active |
| Upload fails | Verify SERVER_HOST / SERVER_PATH; check server is running |
| Short battery life | Increase CAPTURE_INTERVAL_S; check for sleep current leaks |
