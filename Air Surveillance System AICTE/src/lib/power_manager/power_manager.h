/**
 * power_manager.h / .cpp — Battery & Deep Sleep Power Management
 *
 * The LiPo battery (3.7V, ~370mAh) is the primary limiting factor for
 * operational duration (per project results). Deep sleep between capture
 * cycles reduces current from ~160mA (active) to ~10µA (sleep), extending
 * battery life significantly.
 *
 * Deep sleep on ESP32:
 *   esp_deep_sleep_start() — entire CPU halts; wakes on timer or GPIO
 *   RTC memory retains variables across sleep cycles
 *   Camera + SIM800L power off during sleep
 */

#pragma once
#include <Arduino.h>

/**
 * Enter deep sleep for `seconds` seconds, then restart the ESP32.
 * The main loop will re-run on wake (capture → upload → sleep again).
 */
void power_deep_sleep(int seconds);

/**
 * Read approximate battery voltage using the ESP32 ADC.
 * Returns voltage in volts (e.g. 3.85).
 * Note: ESP32-CAM ADC is noisy; this is approximate only.
 *
 * Wiring: Battery + → voltage divider (100kΩ / 100kΩ) → GPIO 33
 */
float power_read_battery_voltage();

/**
 * Returns true if battery is considered low (< 3.5V).
 * At low battery, reduce upload frequency to preserve remaining charge.
 */
bool power_is_battery_low();

/** Print power status to Serial. */
void power_print_status();
