/**
 * gsm_module.cpp — SIM800L / SIM900 GSM Module Implementation
 *
 * Uses AT command set over SoftwareSerial.
 * Sends SMS and initiates voice calls to alert the owner during intrusion.
 */

#include "gsm_module.h"
#include <SoftwareSerial.h>

#define GSM_RX_PIN 10
#define GSM_TX_PIN 11
#define GSM_BAUD   9600

static SoftwareSerial gsmSerial(GSM_RX_PIN, GSM_TX_PIN);

// ─── Internal helpers ─────────────────────────────────────────────────────────
static void sendAT(const char* cmd, unsigned long waitMs = 1000) {
  gsmSerial.println(cmd);
  unsigned long start = millis();
  while (millis() - start < waitMs) {
    if (gsmSerial.available()) {
      Serial.write(gsmSerial.read());
    }
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────
void gsm_init() {
  gsmSerial.begin(GSM_BAUD);
  delay(2000);   // allow SIM800L to boot

  sendAT("AT");            // Test communication
  sendAT("ATE0");          // Turn off echo
  sendAT("AT+CMGF=1");     // Set SMS to text mode
  sendAT("AT+CNMI=1,2,0,0,0");  // New SMS notification

  Serial.println(F("[GSM] SIM800L initialised."));
}

bool gsm_isReady() {
  gsmSerial.println("AT");
  delay(500);
  while (gsmSerial.available()) {
    String resp = gsmSerial.readString();
    if (resp.indexOf("OK") >= 0) return true;
  }
  return false;
}

/**
 * Send an SMS alert to the specified number.
 * Uses AT+CMGS command in text mode.
 */
void gsm_sendSMS(const char* number, const char* message) {
  Serial.println(F("[GSM] Sending SMS..."));

  gsmSerial.print("AT+CMGS=\"");
  gsmSerial.print(number);
  gsmSerial.println("\"");
  delay(500);

  gsmSerial.print(message);
  delay(100);

  gsmSerial.write(26);   // Ctrl+Z — send the SMS
  delay(3000);

  Serial.println(F("[GSM] SMS sent."));
}

/**
 * Initiate a voice call to the specified number.
 * Hangs up automatically after 20 seconds.
 */
void gsm_call(const char* number) {
  Serial.print(F("[GSM] Calling: "));
  Serial.println(number);

  gsmSerial.print("ATD");
  gsmSerial.print(number);
  gsmSerial.println(";");   // Semicolon = voice call (not data)
  delay(20000);              // Let it ring for 20 seconds

  gsm_hangUp();
}

void gsm_hangUp() {
  sendAT("ATH", 1000);
  Serial.println(F("[GSM] Call ended."));
}
