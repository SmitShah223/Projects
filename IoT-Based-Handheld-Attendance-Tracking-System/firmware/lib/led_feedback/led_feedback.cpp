#include "led_feedback.h"

static const int LEDS[] = {LED_GREEN, LED_YELLOW, LED_BLUE, LED_RED};

void led_init() {
  for (int pin : LEDS) { pinMode(pin, OUTPUT); digitalWrite(pin, LOW); }
}

void led_set(int pin) {
  led_off();
  digitalWrite(pin, HIGH);
}

void led_off() {
  for (int pin : LEDS) digitalWrite(pin, LOW);
}

void led_blink(int pin, int times) {
  led_off();
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH); delay(200);
    digitalWrite(pin, LOW);  delay(200);
  }
}
