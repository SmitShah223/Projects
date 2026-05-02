/**
 * fingerprint_handler.h — R307 Fingerprint Sensor Interface
 *
 * Wiring (ESP32 UART2 → R307):
 *   GPIO 16 (RX2) → R307 TX (green)
 *   GPIO 17 (TX2) → R307 RX (white)
 *   3.3–5V        → VCC (red)
 *   GND           → GND (black)
 */

#pragma once
#include <Arduino.h>

typedef enum { FP_MATCH, FP_MISMATCH, FP_TIMEOUT, FP_ERROR } FP_Result;

void      fingerprint_init();
FP_Result fingerprint_scan(int expectedID);

/**
 * Enroll a new fingerprint and store it at position `id` (1-127).
 * Returns true on success.
 */
bool fingerprint_enroll(int id);
