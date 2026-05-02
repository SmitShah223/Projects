/**
 * Smart Door Home Security System
 * Main Arduino Sketch
 *
 * Hardware:
 *   - Arduino UNO (ATmega328P)
 *   - MFRC522 RFID Scanner (SPI)
 *   - 4x4 Matrix Keypad
 *   - SIM800L / SIM900 GSM Module (SoftwareSerial)
 *   - HC-SR04 Ultrasonic Sensor
 *   - SG90 Servo Motor (door lock)
 *   - 16x2 LCD Display (I2C)
 *   - Buzzer (active, GPIO)
 *
 * Two Modes:
 *   INTERNAL MODE — user is inside; only buzzer + LCD alert on intrusion
 *   EXTERNAL MODE — user has left; full GSM SMS + call alert on intrusion
 *
 * Authentication Flow:
 *   1. Tap RFID card → validate UID
 *   2. Enter 4-digit password on keypad
 *   3. Both correct → servo unlocks door
 *   4. Either wrong  → buzzer + LCD alert (3 strikes → GSM alert)
 *
 * Pin Map:
 *   RFID:       SPI (see rfid_handler.h)
 *   Keypad:     Digital 2-9 (rows/cols, see keypad_handler.h)
 *   GSM:        SoftwareSerial RX=10, TX=11
 *   Ultrasonic: Trig=12, Echo=A0
 *   Servo:      D3 (PWM)
 *   LCD:        I2C (SDA=A4, SCL=A5)
 *   Buzzer:     D4
 *   Mode LED:   D5 (GREEN=Internal), D6 (RED=External)
 *
 * Response time under 3 seconds per project results.
 */

#include <Arduino.h>
#include "rfid_handler.h"
#include "keypad_handler.h"
#include "gsm_module.h"
#include "ultrasonic_sensor.h"
#include "servo_lock.h"
#include "lcd_display.h"
#include "buzzer.h"

// ─── System Configuration ─────────────────────────────────────────────────────
#define CORRECT_PASSWORD     "1234"   // Change this to your preferred password
#define MAX_FAILED_ATTEMPTS  3        // Strikes before GSM alert triggers
#define DOOR_UNLOCK_MS       5000     // Door stays unlocked for 5 seconds
#define INTRUSION_DISTANCE   50       // cm — ultrasonic threshold for detection
#define MODE_BTN_PIN         7        // Push button to toggle Internal/External mode
#define LED_INTERNAL_PIN     5        // Green LED — Internal mode indicator
#define LED_EXTERNAL_PIN     6        // Red LED   — External mode indicator
#define OWNER_PHONE          "+91XXXXXXXXXX"  // Replace with owner's number

// ─── Valid RFID UIDs (add authorised cards here) ───────────────────────────────
const char* AUTHORISED_UIDS[] = {
  "A3B2C1D0",
  "12345678",
  // Add more UIDs as needed
};
const int NUM_AUTHORISED = sizeof(AUTHORISED_UIDS) / sizeof(AUTHORISED_UIDS[0]);

// ─── System State ─────────────────────────────────────────────────────────────
typedef enum {
  STATE_IDLE,
  STATE_RFID_OK,
  STATE_PASSWORD_ENTRY,
  STATE_ACCESS_GRANTED,
  STATE_ACCESS_DENIED,
  STATE_INTRUSION,
  STATE_ALERT_SENT
} SystemState;

typedef enum {
  MODE_INTERNAL,
  MODE_EXTERNAL
} SystemMode;

static SystemState state       = STATE_IDLE;
static SystemMode  mode        = MODE_INTERNAL;
static int         failedAttempts = 0;
static unsigned long doorOpenTime = 0;
static String      scannedUID  = "";

// ─── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  Serial.println(F("[BOOT] Smart Door Security System starting..."));

  // Peripheral init
  lcd_init();
  rfid_init();
  keypad_init();
  gsm_init();
  ultrasonic_init();
  servo_init();
  buzzer_init();

  // Mode button + LEDs
  pinMode(MODE_BTN_PIN,     INPUT_PULLUP);
  pinMode(LED_INTERNAL_PIN, OUTPUT);
  pinMode(LED_EXTERNAL_PIN, OUTPUT);

  // Start in internal mode
  setMode(MODE_INTERNAL);

  lcd_showMessage("System Ready", "Tap RFID Card");
  Serial.println(F("[BOOT] Ready."));
}

// ─── Main Loop ────────────────────────────────────────────────────────────────
void loop() {
  // Check mode toggle button
  checkModeButton();

  switch (state) {

    // ── IDLE: waiting for RFID card ────────────────────────────────────────
    case STATE_IDLE:
      // Intrusion detection runs in the background regardless of RFID
      if (intrusionDetected()) {
        handleIntrusion();
        break;
      }
      if (rfid_cardPresent()) {
        scannedUID = rfid_readUID();
        Serial.println("[RFID] Scanned: " + scannedUID);

        if (isAuthorised(scannedUID)) {
          Serial.println(F("[RFID] Authorised card."));
          lcd_showMessage("RFID OK", "Enter Password:");
          state = STATE_RFID_OK;
        } else {
          Serial.println(F("[RFID] Unauthorised card!"));
          lcd_showMessage("RFID INVALID", "Access Denied");
          buzzer_beep(3);
          failedAttempts++;
          checkFailedAttempts();
          delay(2000);
          lcd_showMessage("System Ready", "Tap RFID Card");
        }
      }
      break;

    // ── RFID accepted: prompt password ────────────────────────────────────
    case STATE_RFID_OK:
      state = STATE_PASSWORD_ENTRY;
      break;

    // ── Password entry ─────────────────────────────────────────────────────
    case STATE_PASSWORD_ENTRY: {
      lcd_showMessage("Enter Password:", "____");
      String entered = keypad_getPassword(4);   // blocks until 4 digits entered
      Serial.println("[KEY] Entered: " + entered);

      if (entered == CORRECT_PASSWORD) {
        Serial.println(F("[AUTH] Password correct. Access granted."));
        failedAttempts = 0;
        state = STATE_ACCESS_GRANTED;
      } else {
        Serial.println(F("[AUTH] Wrong password."));
        failedAttempts++;
        lcd_showMessage("Wrong Password!", "Try Again");
        buzzer_beep(2);
        checkFailedAttempts();
        delay(2000);
        state = STATE_IDLE;
        lcd_showMessage("System Ready", "Tap RFID Card");
      }
      break;
    }

    // ── Access granted: unlock door ────────────────────────────────────────
    case STATE_ACCESS_GRANTED:
      lcd_showMessage("Access Granted!", "Door Unlocking");
      buzzer_beep(1);
      servo_unlock();
      doorOpenTime = millis();
      state = STATE_IDLE;
      // Lock door again after DOOR_UNLOCK_MS
      delay(DOOR_UNLOCK_MS);
      servo_lock_door();
      lcd_showMessage("Door Locked", "Tap RFID Card");
      break;

    // ── Intrusion ─────────────────────────────────────────────────────────
    case STATE_INTRUSION:
      // Handled in handleIntrusion() — state resets after alert
      break;

    default:
      state = STATE_IDLE;
      break;
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
bool isAuthorised(const String& uid) {
  for (int i = 0; i < NUM_AUTHORISED; i++) {
    if (uid.equalsIgnoreCase(AUTHORISED_UIDS[i])) return true;
  }
  return false;
}

bool intrusionDetected() {
  long dist = ultrasonic_getDistance();
  return (dist > 0 && dist < INTRUSION_DISTANCE);
}

void handleIntrusion() {
  state = STATE_INTRUSION;
  Serial.println(F("[ALERT] Intrusion detected!"));
  lcd_showMessage("!! INTRUSION !!", "ALERT TRIGGERED");
  buzzer_alarm();

  if (mode == MODE_EXTERNAL) {
    Serial.println(F("[GSM] Sending SMS alert..."));
    gsm_sendSMS(OWNER_PHONE, "ALERT: Intrusion detected at your door! Please check immediately.");
    delay(1000);
    Serial.println(F("[GSM] Calling owner..."));
    gsm_call(OWNER_PHONE);
    state = STATE_ALERT_SENT;
  } else {
    // Internal mode — only buzzer + LCD
    delay(5000);
  }

  buzzer_off();
  state = STATE_IDLE;
  lcd_showMessage("System Ready", "Tap RFID Card");
}

void checkFailedAttempts() {
  if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
    Serial.println(F("[ALERT] Max failed attempts reached!"));
    lcd_showMessage("LOCKOUT!", "Alerting owner...");
    buzzer_alarm();

    if (mode == MODE_EXTERNAL) {
      gsm_sendSMS(OWNER_PHONE, "ALERT: Multiple failed access attempts at your door!");
      delay(500);
      gsm_call(OWNER_PHONE);
    }

    failedAttempts = 0;
    delay(10000);   // 10s lockout period
    buzzer_off();
    lcd_showMessage("System Ready", "Tap RFID Card");
  }
}

void checkModeButton() {
  static bool lastState = HIGH;
  bool current = digitalRead(MODE_BTN_PIN);
  if (lastState == HIGH && current == LOW) {
    // Button pressed — toggle mode
    mode = (mode == MODE_INTERNAL) ? MODE_EXTERNAL : MODE_INTERNAL;
    setMode(mode);
    delay(300);   // debounce
  }
  lastState = current;
}

void setMode(SystemMode m) {
  mode = m;
  if (m == MODE_INTERNAL) {
    digitalWrite(LED_INTERNAL_PIN, HIGH);
    digitalWrite(LED_EXTERNAL_PIN, LOW);
    lcd_showMessage("Mode: INTERNAL", "Tap RFID Card");
    Serial.println(F("[MODE] Internal mode activated."));
  } else {
    digitalWrite(LED_INTERNAL_PIN, LOW);
    digitalWrite(LED_EXTERNAL_PIN, HIGH);
    lcd_showMessage("Mode: EXTERNAL", "Monitoring ON");
    Serial.println(F("[MODE] External mode activated. All sensors active."));
  }
  delay(1500);
  lcd_showMessage("System Ready", "Tap RFID Card");
}
