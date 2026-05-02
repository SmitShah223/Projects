/**
 * keypad_handler.h — 4x4 Matrix Keypad Interface
 *
 * Wiring (Arduino UNO → Keypad):
 *   Row pins:    D2, D3, D4, D5
 *   Column pins: D6, D7, D8, D9 (A1 if D9 conflicts with RFID RST)
 *
 * Layout:
 *   1 2 3 A
 *   4 5 6 B
 *   7 8 9 C
 *   * 0 # D
 *
 * Library: Keypad by Mark Stanley & Alexander Brevig
 */

#pragma once
#include <Arduino.h>

void   keypad_init();
char   keypad_getKey();             // Returns single key press (blocking)
String keypad_getPassword(int len); // Collects `len` digits, displays * on LCD
