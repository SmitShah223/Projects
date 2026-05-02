/**
 * servo_lock.h / .cpp — SG90 Servo Motor Door Lock
 *
 * Controls door lock/unlock via servo rotation.
 *   LOCKED   position: 0°
 *   UNLOCKED position: 90°
 *
 * Wiring (Arduino UNO → SG90 Servo):
 *   Signal (orange) → D3 (PWM)
 *   VCC    (red)    → 5V
 *   GND    (brown)  → GND
 *
 * Library: Servo (built-in Arduino)
 */

#pragma once
#include <Arduino.h>

void servo_init();
void servo_unlock();
void servo_lock_door();
