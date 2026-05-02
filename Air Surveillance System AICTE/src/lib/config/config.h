/**
 * config.h — Central configuration for the Helium Balloon IoT Surveillance System
 *
 * Hardware:
 *   ESP32-CAM (AI-Thinker) — dual-core 32-bit CPU, 4MB PSRAM, OV2640 2MP camera
 *   SIM800L GPRS Module    — Quad-band, GPRS multi-slot class 12
 *   LiPo Battery           — 3.7V (370mAh typical); stepped up to 5V via buck converter
 *   3D-Printed Enclosure   — PLA/ABS casing with camera aperture
 *   Helium Balloon         — provides aerial lift
 *
 * Project: AICTE Air Surveillance System
 * Institution: Thakur College of Engineering & Technology, Mumbai
 * Authors: Smit Shah et al.
 */

#pragma once

// ─── GSM / GPRS Settings ──────────────────────────────────────────────────────
#define GSM_APN          "airtelgprs.com"   // Your SIM card's APN (e.g. "airtelgprs.com", "jionet")
#define GSM_USER         ""                 // APN username (leave blank if none)
#define GSM_PASS         ""                 // APN password (leave blank if none)

// ─── Cloud Server (image upload endpoint) ────────────────────────────────────
// The ESP32 sends an HTTP POST with the captured JPEG to this URL.
// Set up a simple server (Flask / Node.js) or use cloud storage presigned URL.
#define SERVER_HOST      "your-server.example.com"
#define SERVER_PORT      80
#define SERVER_PATH      "/upload"          // endpoint that accepts multipart/form-data

// ─── Capture Settings ─────────────────────────────────────────────────────────
#define CAPTURE_INTERVAL_S  60       // seconds between captures (sleep between cycles)
#define JPEG_QUALITY        12       // 0 = highest quality, 63 = lowest (10-15 is good)
#define FRAME_SIZE          FRAMESIZE_VGA  // VGA 640×480 — good balance of detail vs size

// ─── Deep Sleep ───────────────────────────────────────────────────────────────
// ESP32 enters deep sleep between capture cycles to save battery.
// Deep sleep current: ~10µA vs ~160mA active.
#define ENABLE_DEEP_SLEEP   true
#define uS_TO_S_FACTOR      1000000ULL   // conversion factor for microseconds

// ─── SIM800L UART Pins (ESP32-CAM GPIO) ──────────────────────────────────────
// ⚠️  GPIO 1 (U0TX) and GPIO 3 (U0RX) are the hardware UART0 (also used for Serial).
//     Use GPIO 14 and 15 for SoftwareSerial to avoid conflicts.
#define GSM_RX_PIN  14    // ESP32 GPIO 14 → SIM800L TX
#define GSM_TX_PIN  15    // ESP32 GPIO 15 → SIM800L RX
#define GSM_BAUD    9600

// ─── LED / Status ─────────────────────────────────────────────────────────────
// ESP32-CAM onboard LED (active LOW on GPIO 4 = flash LED)
#define FLASH_LED_PIN   4
#define STATUS_LED_PIN  33   // onboard red LED on AI-Thinker board (active LOW)
