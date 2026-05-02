/**
 * servo_lock.cpp — SG90 Servo Motor Door Lock Implementation
 */

#include "servo_lock.h"
#include <Servo.h>

#define SERVO_PIN      3
#define LOCKED_ANGLE   0
#define UNLOCKED_ANGLE 90

static Servo doorServo;

void servo_init() {
  doorServo.attach(SERVO_PIN);
  doorServo.write(LOCKED_ANGLE);   // ensure locked on boot
  delay(500);
  Serial.println(F("[SERVO] Door servo initialised — locked."));
}

void servo_unlock() {
  Serial.println(F("[SERVO] Unlocking door..."));
  doorServo.write(UNLOCKED_ANGLE);
  delay(500);
}

void servo_lock_door() {
  Serial.println(F("[SERVO] Locking door..."));
  doorServo.write(LOCKED_ANGLE);
  delay(500);
}
