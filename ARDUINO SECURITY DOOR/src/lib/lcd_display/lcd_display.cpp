/**
 * lcd_display.cpp — 16x2 I2C LCD Implementation
 * Library: LiquidCrystal_I2C
 */

#include "lcd_display.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define LCD_ADDR 0x27   // Change to 0x3F if display stays blank
#define LCD_COLS 16
#define LCD_ROWS 2

static LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

void lcd_init() {
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Smart Door");
  lcd.setCursor(0, 1);
  lcd.print("Security System");
  delay(2000);
  lcd.clear();
  Serial.println(F("[LCD] Display ready."));
}

/**
 * Shows a two-line message on the LCD.
 * Strings longer than 16 characters are truncated automatically.
 */
void lcd_showMessage(const char* line1, const char* line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void lcd_clear() {
  lcd.clear();
}
