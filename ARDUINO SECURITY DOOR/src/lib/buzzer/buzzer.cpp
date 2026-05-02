/**
 * buzzer.cpp — Active Buzzer Implementation
 */

#include "buzzer.h"

#define BUZZER_PIN 4

void buzzer_init() {
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println(F("[BUZ] Buzzer ready."));
}

void buzzer_beep(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
  }
}

void buzzer_alarm() {
  // Intermittent alarm for 3 seconds
  unsigned long start = millis();
  while (millis() - start < 3000) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void buzzer_off() {
  digitalWrite(BUZZER_PIN, LOW);
}
