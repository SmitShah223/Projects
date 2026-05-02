/**
 * Helium Balloon-Based IoT Surveillance System
 * Main ESP32-CAM Sketch
 *
 * Operational Flow (per project document Section "Working Principle"):
 *
 *   1. INITIALIZATION   — power on, init camera + GSM module
 *   2. NETWORK          — register on cellular network, open GPRS bearer
 *   3. IMAGE CAPTURE    — OV2640 captures JPEG, stored in PSRAM
 *   4. DATA PROCESSING  — image buffered, filename generated with timestamp
 *   5. TRANSMISSION     — HTTP POST JPEG to cloud server via SIM800L
 *   6. REMOTE ACCESS    — image available on server for remote viewing
 *   7. DEEP SLEEP       — enter low-power sleep for CAPTURE_INTERVAL_S seconds
 *                         (10µA sleep vs 160mA active — critical for battery life)
 *   8. REPEAT (wake + restart from step 1)
 *
 * Hardware:
 *   ESP32-CAM (AI-Thinker) — OV2640 2MP, 4MB PSRAM
 *   SIM800L GPRS Module    — Quad-band GSM, GPRS class 12
 *   LiPo 3.7V battery      — stepped to 5V via buck converter
 *   3D-printed PLA casing  — camera aperture + antenna ports
 *   Helium balloon         — aerial lift platform
 *
 * Project: AICTE Air Surveillance System
 * Institution: Thakur College of Engineering & Technology, Mumbai
 */

#include <Arduino.h>
#include "camera.h"
#include "gsm_gprs.h"
#include "power_manager.h"
#include "config.h"

// ─── LED helpers ─────────────────────────────────────────────────────────────
static void led_on()  { digitalWrite(STATUS_LED_PIN, LOW);  }   // Active LOW
static void led_off() { digitalWrite(STATUS_LED_PIN, HIGH); }
static void led_blink(int n, int ms = 200) {
  for (int i = 0; i < n; i++) {
    led_on(); delay(ms); led_off(); delay(ms);
  }
}

// ─── Generate filename from boot count ───────────────────────────────────────
// Uses RTC boot counter since ESP32-CAM has no RTC clock by default.
// Filename format: "img_0042.jpg"
static void make_filename(char* buf, size_t len) {
  extern RTC_DATA_ATTR int uploadCount;
  snprintf(buf, len, "img_%04d.jpg", uploadCount);
}

// ─── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n===================================="));
  Serial.println(F("  Helium Balloon IoT Surveillance"));
  Serial.println(F("===================================="));

  // Status LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  led_off();

  // ── Step 1: Print power / boot status ─────────────────────────────────────
  power_print_status();

  // Reduce upload frequency on low battery
  int sleep_interval = CAPTURE_INTERVAL_S;
  if (power_is_battery_low()) {
    sleep_interval = CAPTURE_INTERVAL_S * 3;
    Serial.printf("[MAIN] Low battery — extending sleep to %ds\n", sleep_interval);
  }

  // ── Step 2: Initialise camera ──────────────────────────────────────────────
  led_blink(1, 100);
  Serial.println(F("[MAIN] Initialising camera..."));
  if (!camera_init()) {
    Serial.println(F("[MAIN] ❌ Camera init failed. Sleeping and retrying."));
    led_blink(5, 100);
    power_deep_sleep(sleep_interval);
    return;
  }

  // Warm up the camera — discard 3 frames for exposure stabilisation
  camera_warmup(3);

  // ── Step 3: Capture image ─────────────────────────────────────────────────
  Serial.println(F("[MAIN] Capturing image..."));
  led_on();
  camera_fb_t* fb = camera_capture();
  led_off();

  if (!fb) {
    Serial.println(F("[MAIN] ❌ Capture failed. Sleeping."));
    led_blink(3, 100);
    power_deep_sleep(sleep_interval);
    return;
  }

  Serial.printf("[MAIN] Image size: %zu bytes\n", fb->len);

  // Copy JPEG from frame buffer to heap so we can release the camera early
  uint8_t* imgData = (uint8_t*)ps_malloc(fb->len);  // allocate in PSRAM
  size_t   imgLen  = fb->len;
  if (!imgData) imgData = (uint8_t*)malloc(fb->len); // fallback to DRAM

  if (!imgData) {
    Serial.println(F("[MAIN] ❌ Memory allocation failed."));
    camera_release_frame(fb);
    power_deep_sleep(sleep_interval);
    return;
  }

  memcpy(imgData, fb->buf, fb->len);
  camera_release_frame(fb);   // Release camera buffer early

  // ── Step 4: Initialise GSM and connect GPRS ───────────────────────────────
  Serial.println(F("[MAIN] Initialising GSM module..."));
  led_blink(2, 150);

  if (!gsm_init()) {
    Serial.println(F("[MAIN] ❌ GSM init failed. Sleeping."));
    free(imgData);
    led_blink(6, 100);
    power_deep_sleep(sleep_interval);
    return;
  }

  Serial.printf("[MAIN] Signal strength: %d/31\n", gsm_signal_strength());

  if (!gsm_gprs_connect()) {
    Serial.println(F("[MAIN] ❌ GPRS connection failed. Sleeping."));
    free(imgData);
    led_blink(4, 100);
    power_deep_sleep(sleep_interval);
    return;
  }

  // ── Step 5: Upload image via HTTP POST ────────────────────────────────────
  char filename[20];
  make_filename(filename, sizeof(filename));

  Serial.printf("[MAIN] Uploading '%s' (%zu bytes) to %s%s...\n",
                filename, imgLen, SERVER_HOST, SERVER_PATH);

  led_blink(1, 50);
  bool uploaded = gsm_http_post_image(imgData, imgLen, filename);
  free(imgData);

  if (uploaded) {
    led_blink(3, 100);   // 3 blinks = success
    Serial.println(F("[MAIN] ✅ Upload complete. Image available on cloud server."));
  } else {
    led_blink(6, 50);    // 6 rapid blinks = failure
    Serial.println(F("[MAIN] ❌ Upload failed."));
  }

  // ── Step 6: Disconnect GPRS ───────────────────────────────────────────────
  gsm_gprs_disconnect();

  // ── Step 7: Enter deep sleep ──────────────────────────────────────────────
  Serial.printf("[MAIN] Sleeping for %d seconds...\n", sleep_interval);
  Serial.flush();
  led_off();
  power_deep_sleep(sleep_interval);

  // Code never reaches here — ESP32 restarts on timer wake
}

void loop() {
  // All work is done in setup().
  // After deep sleep, the ESP32 restarts and setup() runs again.
  // This loop() is only reached if ENABLE_DEEP_SLEEP is false (debug mode).
  Serial.println(F("[MAIN] Loop running (deep sleep disabled — debug mode)."));
  delay(CAPTURE_INTERVAL_S * 1000UL);
  ESP.restart();
}
