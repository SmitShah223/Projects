/**
 * buzzer.h / .cpp — Active Buzzer Interface
 *
 * Wiring (Arduino UNO → Active Buzzer):
 *   + → D4 (through a 100Ω resistor)
 *   – → GND
 *
 * Active buzzer: sounds when pin is HIGH. No frequency needed.
 */

#pragma once
#include <Arduino.h>

void buzzer_init();
void buzzer_beep(int times);   // short beeps (200ms each)
void buzzer_alarm();           // continuous alarm (3 seconds)
void buzzer_off();
