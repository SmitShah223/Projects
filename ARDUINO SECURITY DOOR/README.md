# Smart Door Home Security System

> **Hardware:** Arduino UNO · RFID (MFRC522) · GSM (SIM800L) · HC-SR04 · SG90 Servo · 16×2 LCD · 4×4 Keypad  
> **Response time:** < 3 seconds  
> **Authentication:** Dual-layer — RFID card + 4-digit password

---

## Overview

An IoT-based smart door security system built around the Arduino UNO. It authenticates users through a **dual-layer system** (RFID card + keypad password) and instantly alerts the owner via **SMS and voice call** using a GSM module when unauthorized access is attempted or the ultrasonic sensor detects an intruder.

Two operational modes handle both when the user is home (internal) and away (external), with appropriate escalation in each case.

---

## Features

| Feature | Detail |
|---|---|
| Dual authentication | RFID card UID + 4-digit keypad password — both must pass |
| GSM alerts | SMS + voice call to owner on intrusion (external mode) |
| Ultrasonic detection | HC-SR04 detects presence within 50 cm |
| Servo door lock | SG90 rotates 0°→90° to unlock, auto-relocks after 5s |
| Two modes | Internal (buzzer only) / External (full GSM alert) |
| LCD feedback | 16×2 display shows all system states |
| Lockout | 3 failed attempts → GSM alert + 10s lockout |
| Response time | < 3 seconds (per test results) |

---

## Hardware Components

| Component | Model | Interface |
|---|---|---|
| Microcontroller | Arduino UNO (ATmega328P) | — |
| RFID Scanner | MFRC522 RC522 | SPI |
| GSM Module | SIM800L / SIM900 | SoftwareSerial |
| Ultrasonic Sensor | HC-SR04 | Digital GPIO |
| Servo Motor | SG90 | PWM (D3) |
| LCD Display | 16×2 with I2C backpack | I2C (A4/A5) |
| Keypad | 4×4 Matrix | Digital GPIO |
| Buzzer | Active buzzer | Digital GPIO (D4) |

---

## Pin Map

| Component | Arduino Pin |
|---|---|
| RFID SDA (CS) | D10 |
| RFID SCK | D13 |
| RFID MOSI | D11 |
| RFID MISO | D12 |
| RFID RST | D9 |
| Keypad Row 1-4 | D2, D3, D4, D5 |
| Keypad Col 1-4 | D6, D7, D8, A1 |
| GSM RX | D10 *(shared via SoftwareSerial — see note)* |
| GSM TX | D11 |
| Ultrasonic TRIG | D12 |
| Ultrasonic ECHO | A0 |
| Servo Signal | D3 |
| LCD SDA | A4 |
| LCD SCL | A5 |
| Buzzer | D4 |
| Mode button | D7 |
| LED Internal | D5 |
| LED External | D6 |

> **Note on SoftwareSerial:** GSM and RFID share some pins due to Arduino UNO's limited I/O. In the final build, use an Arduino Mega for more serial ports, or time-multiplex the GSM communication to avoid conflicts.

---

## Repository Structure

```
ARDUINO SECURITY DOOR/
├── src/
│   ├── main/
│   │   └── main.ino                    # Main sketch — full system logic
│   └── lib/
│       ├── rfid_handler/               # MFRC522 RFID driver
│       │   ├── rfid_handler.h
│       │   └── rfid_handler.cpp
│       ├── keypad_handler/             # 4x4 matrix keypad driver
│       │   ├── keypad_handler.h
│       │   └── keypad_handler.cpp
│       ├── gsm_module/                 # SIM800L GSM SMS + call driver
│       │   ├── gsm_module.h
│       │   └── gsm_module.cpp
│       ├── ultrasonic_sensor/          # HC-SR04 distance measurement
│       │   ├── ultrasonic_sensor.h
│       │   └── ultrasonic_sensor.cpp
│       ├── servo_lock/                 # SG90 servo door lock driver
│       │   ├── servo_lock.h
│       │   └── servo_lock.cpp
│       ├── lcd_display/               # 16x2 I2C LCD driver
│       │   ├── lcd_display.h
│       │   └── lcd_display.cpp
│       └── buzzer/                    # Active buzzer driver
│           ├── buzzer.h
│           └── buzzer.cpp
│
├── docs/
│   └── smart-door-home-security-system.pdf
│
├── media/
│   └── demo.mp4
│
├── .gitignore
└── README.md
```

---

## System Flow

```
Power ON → Initialize all modules → System Ready
                    │
           Tap RFID Card
                    │
          UID in whitelist? ─── No ──► Buzzer ×3 → count failed attempt
                    │ Yes
                    ▼
          Enter 4-digit password
                    │
          Password correct? ─── No ──► Buzzer ×2 → count failed attempt
                    │ Yes                  │
                    ▼                 Failed × 3?
          Servo unlocks (90°)             │ Yes
          LCD: "Access Granted"           ▼
          Door open for 5s          GSM alert (if External)
          Servo re-locks (0°)       10s lockout
                    │
           Background loop:
           Ultrasonic < 50cm?
                    │ Yes
                    ▼
        INTERNAL MODE       EXTERNAL MODE
        Buzzer alarm         Buzzer alarm
        LCD warning          LCD warning
                             SMS to owner
                             Voice call to owner
```

---

## Configuration (in `main.ino`)

```cpp
#define CORRECT_PASSWORD    "1234"     // Your 4-digit password
#define MAX_FAILED_ATTEMPTS 3          // Strikes before GSM alert
#define DOOR_UNLOCK_MS      5000       // ms door stays unlocked
#define INTRUSION_DISTANCE  50         // cm trigger threshold
#define OWNER_PHONE         "+91XXXXXXXXXX"  // Your phone number

// Authorised RFID UIDs (find yours via Serial Monitor)
const char* AUTHORISED_UIDS[] = { "A3B2C1D0", "12345678" };
```

---

## Quick Start

### 1. Install Arduino Libraries

Open Arduino IDE → Tools → Manage Libraries → install:
- `MFRC522` by miguelbalboa
- `Keypad` by Mark Stanley & Alexander Brevig
- `LiquidCrystal_I2C` by Frank de Brabander
- `Servo` (built-in)
- `SoftwareSerial` (built-in)

### 2. Find Your RFID Card UID

Upload this temporary sketch to print your card's UID:
```cpp
#include <SPI.h>
#include <MFRC522.h>
MFRC522 rfid(10, 9);
void setup() { Serial.begin(9600); SPI.begin(); rfid.PCD_Init(); }
void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;
  for (byte i = 0; i < rfid.uid.size; i++) Serial.print(rfid.uid.uidByte[i], HEX);
  Serial.println();
}
```
Add the printed UID to `AUTHORISED_UIDS[]` in `main.ino`.

### 3. Set Your Phone Number

Replace `+91XXXXXXXXXX` with your number in `main.ino`.

### 4. Upload

Open `src/main/main.ino` in Arduino IDE → select **Arduino UNO** → Upload.

### 5. Test

1. Tap your RFID card → LCD shows "RFID OK"
2. Enter `1234` on keypad → LCD shows "Access Granted"
3. Servo rotates 90° → door unlocks → relocks after 5s
4. Toggle mode button to switch Internal ↔ External
5. Walk past the ultrasonic in External mode → SMS + call fired

---

## SIM800L Power Note

⚠️ The SIM800L draws up to **2A peak** during TX. Power it from a dedicated **4.2V LiPo** or a **5V 2A adapter with a voltage divider** — never from the Arduino 5V pin (max 500mA from USB).
