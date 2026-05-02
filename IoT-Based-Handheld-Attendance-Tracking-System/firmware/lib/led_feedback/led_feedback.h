/**
 * led_feedback.h / led_feedback.cpp — LED Status Indicator
 *
 * Uses 3 LEDs (Green, Yellow/Amber, Red, Blue) on GPIO pins to
 * communicate system state to the user without a display.
 *
 *   GREEN   — Ready / authenticated
 *   YELLOW  — Processing
 *   BLUE    — Waiting for fingerprint
 *   RED     — Rejected / error
 */

#pragma once
#include <Arduino.h>

#define LED_GREEN  25
#define LED_YELLOW 26
#define LED_BLUE   27
#define LED_RED    14

void led_init();
void led_set(int pin);
void led_off();
void led_blink(int pin, int times);
