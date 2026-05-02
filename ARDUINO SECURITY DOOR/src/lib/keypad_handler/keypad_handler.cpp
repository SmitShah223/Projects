/**
 * keypad_handler.cpp — 4x4 Matrix Keypad Implementation
 * Library: Keypad by Mark Stanley & Alexander Brevig
 */

#include "keypad_handler.h"
#include "lcd_display.h"
#include <Keypad.h>

#define ROWS 4
#define COLS 4

static char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// Row pins: D2, D3, D4, D5   (adjust if conflicts exist)
// Col pins: D6, D7, D8, D9
static byte rowPins[ROWS] = {2, 3, 4, 5};
static byte colPins[COLS]  = {6, 7, 8, A1};  // A1 used to avoid D9 conflict with RFID RST

static Keypad kpd(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void keypad_init() {
  // Keypad library handles pin setup internally
  Serial.println(F("[KPD] Keypad ready."));
}

char keypad_getKey() {
  char key = NO_KEY;
  while (key == NO_KEY) {
    key = kpd.getKey();
    delay(50);
  }
  return key;
}

/**
 * Blocks until exactly `len` digit keys are pressed.
 * Displays asterisks on the LCD for each entered digit.
 * '#' clears the entry; '*' submits early.
 */
String keypad_getPassword(int len) {
  String password = "";
  String masked   = "";

  lcd_showMessage("Enter Password:", "");

  while ((int)password.length() < len) {
    char key = kpd.getKey();
    if (key == NO_KEY) { delay(50); continue; }

    if (key >= '0' && key <= '9') {
      password += key;
      masked   += '*';
      lcd_showMessage("Enter Password:", masked);
      Serial.print('*');
    } else if (key == '#') {
      // Clear entry
      password = "";
      masked   = "";
      lcd_showMessage("Cleared", "Enter Password:");
      delay(500);
      lcd_showMessage("Enter Password:", "");
    }
    // Ignore other keys during password entry
  }
  Serial.println();
  return password;
}
