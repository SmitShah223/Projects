/**
 * power_manager.cpp — ESP32 Deep Sleep + Battery ADC
 */

#include "power_manager.h"
#include "config.h"

// Battery ADC — connect via 100kΩ/100kΩ voltage divider to GPIO 33
#define BATTERY_ADC_PIN    33
#define BATTERY_LOW_V      3.50f
#define BATTERY_FULL_V     4.20f
#define ADC_REF_V          3.3f
#define ADC_MAX            4095.0f
#define DIVIDER_RATIO      2.0f    // 100k/(100k+100k) = 0.5 → multiply ADC reading by 2

// RTC memory — persists across deep sleep cycles
RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR int uploadCount = 0;

void power_deep_sleep(int seconds) {
  Serial.printf("[PWR] Entering deep sleep for %d seconds...\n", seconds);
  Serial.flush();

  // Configure wake-up timer
  esp_sleep_enable_timer_wakeup((uint64_t)seconds * uS_TO_S_FACTOR);
  esp_deep_sleep_start();
  // Code never reaches here — ESP32 restarts on wake
}

float power_read_battery_voltage() {
  // Average several ADC readings to reduce noise
  long sum = 0;
  for (int i = 0; i < 16; i++) {
    sum += analogRead(BATTERY_ADC_PIN);
    delay(2);
  }
  float adc_avg  = sum / 16.0f;
  float adc_volt = (adc_avg / ADC_MAX) * ADC_REF_V;
  float batt_v   = adc_volt * DIVIDER_RATIO;
  return batt_v;
}

bool power_is_battery_low() {
  return power_read_battery_voltage() < BATTERY_LOW_V;
}

void power_print_status() {
  bootCount++;
  uploadCount++;

  float v   = power_read_battery_voltage();
  int   pct = constrain((int)((v - BATTERY_LOW_V) / (BATTERY_FULL_V - BATTERY_LOW_V) * 100), 0, 100);

  Serial.println(F("─────────────────────────────"));
  Serial.printf("[PWR] Boot count  : %d\n", bootCount);
  Serial.printf("[PWR] Upload count: %d\n", uploadCount);
  Serial.printf("[PWR] Battery     : %.2fV (~%d%%)\n", v, pct);
  if (power_is_battery_low()) {
    Serial.println(F("[PWR] ⚠️  Low battery! Reduce capture frequency."));
  }
  Serial.println(F("─────────────────────────────"));
}
