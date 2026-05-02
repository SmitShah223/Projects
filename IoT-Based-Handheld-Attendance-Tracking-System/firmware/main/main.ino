/**
 * IoT-Based Handheld Attendance Tracking System
 * ESP32 Firmware — Main Entry Point
 *
 * Hardware:
 *   - ESP32 DevKit Module
 *   - MFRC522 RC522 RFID Reader (SPI)
 *   - R307 Fingerprint Sensor (UART)
 *   - Li-ion Battery + Charging Module
 *
 * Flow:
 *   1. Scan RFID card  → validate UID against local cache
 *   2. If RFID valid   → prompt fingerprint scan
 *   3. Validate fingerprint template stored in R307
 *   4. If both valid   → log attendance to SPIFFS/local storage
 *   5. When Wi-Fi up   → sync local log to AWS IoT Core via MQTT
 *
 * Published: ICCDS February 2024 (ISBN: 979-8-9879839-7-3)
 * Authors:   Darshit Shah, Parthav Shah, Smit Shah
 * Guide:     Mr. Sunil Khatri, Dept. of IoT, TCET Mumbai
 */

#include <Arduino.h>
#include "rfid_handler.h"
#include "fingerprint_handler.h"
#include "wifi_mqtt.h"
#include "local_storage.h"
#include "led_feedback.h"

// ─── System States ────────────────────────────────────────────────────────────
typedef enum {
  STATE_IDLE,
  STATE_RFID_SCANNED,
  STATE_FP_PROMPTED,
  STATE_AUTHENTICATED,
  STATE_REJECTED,
  STATE_SYNCING
} SystemState;

static SystemState systemState   = STATE_IDLE;
static String      currentUID    = "";
static int         currentStudent = -1;
static unsigned long lastSyncMs  = 0;

const unsigned long SYNC_INTERVAL_MS = 60000UL;   // 60 s

// ─── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n[BOOT] IoT Attendance System starting…"));

  led_init();
  led_set(LED_YELLOW);        // booting

  rfid_init();                // SPI + MFRC522
  fingerprint_init();         // UART2 + R307
  storage_init();             // SPIFFS + JSON log
  wifi_mqtt_init();           // Wi-Fi + AWS IoT Core

  led_set(LED_GREEN);
  Serial.println(F("[BOOT] Ready. Waiting for RFID card…"));
}

// ─── Main Loop ────────────────────────────────────────────────────────────────
void loop() {
  wifi_mqtt_loop();           // keep MQTT alive; handle cloud messages

  switch (systemState) {

    // ── IDLE: waiting for card ──────────────────────────────────────────────
    case STATE_IDLE:
      if (rfid_cardPresent()) {
        currentUID = rfid_readUID();
        Serial.println("[RFID] Detected UID: " + currentUID);
        led_set(LED_YELLOW);

        currentStudent = storage_lookupUID(currentUID);
        if (currentStudent >= 0) {
          Serial.println("[RFID] Valid — Student ID: " + String(currentStudent));
          systemState = STATE_RFID_SCANNED;
        } else {
          Serial.println(F("[RFID] Unknown card. Rejected."));
          led_blink(LED_RED, 3);
          systemState = STATE_REJECTED;
        }
      }
      break;

    // ── RFID OK: prompt fingerprint ─────────────────────────────────────────
    case STATE_RFID_SCANNED:
      Serial.println(F("[FP] Place finger on sensor…"));
      led_set(LED_BLUE);
      systemState = STATE_FP_PROMPTED;
      break;

    // ── Fingerprint scan ────────────────────────────────────────────────────
    case STATE_FP_PROMPTED: {
      FP_Result r = fingerprint_scan(currentStudent);
      if (r == FP_MATCH) {
        Serial.println(F("[FP] Match! Authentication successful."));
        systemState = STATE_AUTHENTICATED;
      } else if (r == FP_TIMEOUT) {
        Serial.println(F("[FP] Timeout — try again."));
        led_blink(LED_RED, 2);
        systemState = STATE_IDLE;
      } else {
        Serial.println(F("[FP] Mismatch. Rejected."));
        led_blink(LED_RED, 3);
        systemState = STATE_REJECTED;
      }
      break;
    }

    // ── Both checks passed: log attendance ──────────────────────────────────
    case STATE_AUTHENTICATED: {
      String ts = get_timestamp();
      storage_logAttendance(currentStudent, currentUID, ts);
      Serial.printf("[ATT] StudentID=%d  UID=%s  Time=%s\n",
                    currentStudent, currentUID.c_str(), ts.c_str());
      led_blink(LED_GREEN, 2);

      if (wifi_isConnected())
        mqtt_publishAttendance(currentStudent, currentUID, ts);

      currentUID     = "";
      currentStudent = -1;
      systemState    = STATE_IDLE;
      led_set(LED_GREEN);
      break;
    }

    // ── Rejected: pause then reset ──────────────────────────────────────────
    case STATE_REJECTED:
      delay(1500);
      systemState = STATE_IDLE;
      led_set(LED_GREEN);
      break;

    default:
      systemState = STATE_IDLE;
      break;
  }

  // Periodic background sync of locally stored (offline) records
  if (wifi_isConnected() && (millis() - lastSyncMs > SYNC_INTERVAL_MS)) {
    mqtt_syncPendingRecords();
    lastSyncMs = millis();
  }
}
