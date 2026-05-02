/**
 * lcd_display.h / .cpp — 16x2 LCD Display via I2C
 *
 * Uses a PCF8574 I2C backpack on the LCD (most 16x2 modules come with it).
 * Default I2C address: 0x27 (some modules use 0x3F — check with i2c_scanner)
 *
 * Wiring (Arduino UNO → I2C LCD Backpack):
 *   SDA → A4
 *   SCL → A5
 *   VCC → 5V
 *   GND → GND
 *
 * Library: LiquidCrystal_I2C by Frank de Brabander
 *          (install via Arduino Library Manager)
 */

#pragma once
#include <Arduino.h>

void lcd_init();
void lcd_showMessage(const char* line1, const char* line2);
void lcd_clear();
