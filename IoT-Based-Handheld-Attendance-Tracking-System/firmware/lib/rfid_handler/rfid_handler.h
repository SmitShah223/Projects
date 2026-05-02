/**
 * rfid_handler.h — RC522 MFRC522 RFID Reader Interface
 *
 * Wiring (ESP32 → RC522):
 *   GPIO 5  → SDA (SS/CS)
 *   GPIO 18 → SCK
 *   GPIO 23 → MOSI
 *   GPIO 19 → MISO
 *   GPIO 0  → RST
 *   3.3V    → 3.3V
 *   GND     → GND
 */

#pragma once
#include <Arduino.h>

void   rfid_init();
bool   rfid_cardPresent();
String rfid_readUID();
