/**
 * ultrasonic_sensor.cpp — HC-SR04 Ultrasonic Sensor Implementation
 */

#include "ultrasonic_sensor.h"

#define TRIG_PIN  12
#define ECHO_PIN  A0

void ultrasonic_init() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.println(F("[US] Ultrasonic sensor ready."));
}

/**
 * Measures distance using the HC-SR04 echo timing method.
 *
 * Pulse timing:
 *   1. Pull TRIG LOW for 2us
 *   2. Pull TRIG HIGH for 10us
 *   3. Measure ECHO pulse duration
 *   4. Distance (cm) = duration / 58.2
 *
 * Returns -1 if no echo received within 30ms (out of range or error).
 */
long ultrasonic_getDistance() {
  // Ensure TRIG is clean
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  // Send 10us pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure ECHO pulse (timeout = 30ms → ~500cm max)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) return -1;

  long distance = duration / 58L;   // Convert to cm
  return distance;
}
