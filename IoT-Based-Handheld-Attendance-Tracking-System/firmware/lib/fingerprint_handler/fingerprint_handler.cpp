/**
 * fingerprint_handler.cpp — R307 Fingerprint Sensor Implementation
 * Library: Adafruit Fingerprint Sensor Library
 *
 * The R307 sensor stores up to 127 fingerprint templates internally.
 * Each student is enrolled once and their template is saved at slot = studentID.
 * During attendance, the sensor performs a 1:1 verification against the
 * expected student's stored template.
 */

#include "fingerprint_handler.h"
#include <Adafruit_Fingerprint.h>

#define FP_UART_RX 16
#define FP_UART_TX 17
#define FP_BAUD    57600
#define FP_TIMEOUT_MS 10000

static HardwareSerial fpSerial(2);
static Adafruit_Fingerprint finger(&fpSerial);

void fingerprint_init() {
  fpSerial.begin(FP_BAUD, SERIAL_8N1, FP_UART_RX, FP_UART_TX);
  finger.begin(FP_BAUD);

  if (finger.verifyPassword()) {
    Serial.println(F("[FP] R307 sensor found and verified."));
  } else {
    Serial.println(F("[FP] ERROR: R307 not found — check wiring!"));
    while (true) delay(1000);
  }
  Serial.printf("[FP] Capacity: %d templates\n", finger.capacity);
}

/**
 * Scan finger and verify it matches the template stored at `expectedID`.
 *
 * Returns:
 *   FP_MATCH     — finger matched the expected template
 *   FP_MISMATCH  — finger found but does not match expectedID
 *   FP_TIMEOUT   — no finger detected within FP_TIMEOUT_MS
 *   FP_ERROR     — sensor communication error
 */
FP_Result fingerprint_scan(int expectedID) {
  unsigned long start = millis();

  // Wait for a finger to be placed
  while (finger.getImage() != FINGERPRINT_OK) {
    if (millis() - start > FP_TIMEOUT_MS) return FP_TIMEOUT;
    delay(50);
  }

  // Convert image to feature template
  if (finger.image2Tz() != FINGERPRINT_OK) return FP_ERROR;

  // Search all stored templates
  if (finger.fingerSearch() != FINGERPRINT_OK) return FP_MISMATCH;

  // Check if the best match is our expected student
  if (finger.fingerID == expectedID) return FP_MATCH;

  return FP_MISMATCH;
}

/**
 * Enroll a new fingerprint at slot `id`.
 * The sensor captures the finger twice for robustness.
 */
bool fingerprint_enroll(int id) {
  Serial.printf("[FP] Enrolling fingerprint at slot %d\n", id);

  // --- First capture ---
  Serial.println(F("[FP] Place finger on sensor (1st time)…"));
  while (finger.getImage() != FINGERPRINT_OK) delay(100);
  if (finger.image2Tz(1) != FINGERPRINT_OK) { Serial.println(F("[FP] Image 1 failed.")); return false; }

  Serial.println(F("[FP] Remove finger…"));
  delay(2000);
  while (finger.getImage() != FINGERPRINT_NOFINGER) delay(200);

  // --- Second capture ---
  Serial.println(F("[FP] Place finger again (2nd time)…"));
  while (finger.getImage() != FINGERPRINT_OK) delay(100);
  if (finger.image2Tz(2) != FINGERPRINT_OK) { Serial.println(F("[FP] Image 2 failed.")); return false; }

  // Create model from both captures
  if (finger.createModel() != FINGERPRINT_OK) { Serial.println(F("[FP] Model creation failed.")); return false; }

  // Store model at the given ID slot
  if (finger.storeModel(id) != FINGERPRINT_OK) { Serial.println(F("[FP] Store failed.")); return false; }

  Serial.printf("[FP] Fingerprint enrolled at slot %d\n", id);
  return true;
}
