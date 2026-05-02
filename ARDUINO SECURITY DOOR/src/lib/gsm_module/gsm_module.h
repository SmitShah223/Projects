/**
 * gsm_module.h — SIM800L / SIM900 GSM Module Interface
 *
 * Wiring (Arduino UNO → SIM800L):
 *   SoftwareSerial TX → D11
 *   SoftwareSerial RX → D10
 *   VCC → 4.2V (use a separate LiPo or DC-DC converter — SIM800L needs ~2A peak!)
 *   GND → GND (shared with Arduino)
 *
 * ⚠️ IMPORTANT: SIM800L draws up to 2A on TX burst. Do NOT power from Arduino 5V pin.
 *    Use a 18650 LiPo cell or a 5V 2A adapter with a voltage divider to 4.2V.
 *
 * Library: SoftwareSerial (built-in Arduino)
 */

#pragma once
#include <Arduino.h>

void gsm_init();
void gsm_sendSMS(const char* number, const char* message);
void gsm_call(const char* number);
void gsm_hangUp();
bool gsm_isReady();
