/**
 * rfid_handler.h — MFRC522 RFID Scanner Interface
 *
 * Wiring (Arduino UNO → MFRC522):
 *   Pin 10 → SDA (SS/CS)
 *   Pin 13 → SCK
 *   Pin 11 → MOSI
 *   Pin 12 → MISO
 *   Pin 9  → RST
 *   3.3V   → 3.3V  ← IMPORTANT: MFRC522 is 3.3V only!
 *   GND    → GND
 *
 * Library: MFRC522 by miguelbalboa (install via Arduino Library Manager)
 */

#pragma once
#include <Arduino.h>

void   rfid_init();
bool   rfid_cardPresent();
String rfid_readUID();
