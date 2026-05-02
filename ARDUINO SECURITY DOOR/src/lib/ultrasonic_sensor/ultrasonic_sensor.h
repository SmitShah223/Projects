/**
 * ultrasonic_sensor.h / .cpp — HC-SR04 Ultrasonic Sensor
 *
 * Detects presence/motion near the door.
 * Returns distance in cm. Returns -1 on timeout/error.
 *
 * Wiring (Arduino UNO → HC-SR04):
 *   Trig → D12
 *   Echo → A0  (analog pin used as digital input)
 *   VCC  → 5V
 *   GND  → GND
 *
 * Detection threshold: < 50 cm (set in main.ino as INTRUSION_DISTANCE)
 */

#pragma once
#include <Arduino.h>

void gsm_init();
long ultrasonic_getDistance();   // returns distance in cm; -1 on error
