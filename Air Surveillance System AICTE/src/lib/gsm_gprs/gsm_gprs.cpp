/**
 * gsm_gprs.cpp — SIM800L GSM/GPRS Implementation
 *
 * Uses SoftwareSerial on GPIO 14/15 to communicate with the SIM800L.
 * Sends AT commands to:
 *   1. Verify module is alive (AT)
 *   2. Register on network (AT+CREG)
 *   3. Configure APN (AT+SAPBR)
 *   4. Open HTTP session (AT+HTTPINIT)
 *   5. POST JPEG data (AT+HTTPDATA, AT+HTTPACTION)
 *   6. Read HTTP response code
 */

#include "gsm_gprs.h"
#include "config.h"
#include <SoftwareSerial.h>

static SoftwareSerial gsmSerial(GSM_RX_PIN, GSM_TX_PIN);

// ─── Internal helpers ─────────────────────────────────────────────────────────
static String _readResponse(unsigned long timeout = 2000) {
  String resp = "";
  unsigned long start = millis();
  while (millis() - start < timeout) {
    while (gsmSerial.available()) {
      char c = gsmSerial.read();
      resp += c;
    }
  }
  return resp;
}

static bool _waitForResponse(const char* expected, unsigned long timeout = 5000) {
  unsigned long start = millis();
  String resp = "";
  while (millis() - start < timeout) {
    while (gsmSerial.available()) {
      resp += (char)gsmSerial.read();
    }
    if (resp.indexOf(expected) >= 0) return true;
  }
  Serial.print(F("[GSM] Timeout waiting for: "));
  Serial.println(expected);
  return false;
}

// ─── Public API ───────────────────────────────────────────────────────────────
void gsm_send_at(const char* cmd, unsigned long waitMs) {
  gsmSerial.println(cmd);
  delay(waitMs);
  while (gsmSerial.available()) Serial.write(gsmSerial.read());
}

bool gsm_init() {
  gsmSerial.begin(GSM_BAUD);
  delay(3000);   // SIM800L boot time

  Serial.println(F("[GSM] Initialising SIM800L..."));

  // Test AT communication
  for (int i = 0; i < 5; i++) {
    gsmSerial.println("AT");
    delay(500);
    String r = _readResponse(500);
    if (r.indexOf("OK") >= 0) break;
    if (i == 4) { Serial.println(F("[GSM] No response!")); return false; }
  }

  gsm_send_at("ATE0");           // Disable echo
  gsm_send_at("AT+CMEE=2");      // Extended error codes
  gsm_send_at("AT+CPIN?");       // Check SIM card

  // Wait for network registration (up to 60s)
  Serial.println(F("[GSM] Waiting for network registration..."));
  for (int i = 0; i < 30; i++) {
    gsmSerial.println("AT+CREG?");
    String r = _readResponse(1000);
    // +CREG: 0,1 = registered home; +CREG: 0,5 = registered roaming
    if (r.indexOf(",1") >= 0 || r.indexOf(",5") >= 0) {
      Serial.println(F("[GSM] Registered on network."));
      // Print signal strength
      gsmSerial.println("AT+CSQ");
      Serial.print(F("[GSM] Signal: "));
      Serial.println(_readResponse(500));
      return true;
    }
    delay(2000);
  }
  Serial.println(F("[GSM] Network registration failed."));
  return false;
}

bool gsm_gprs_connect() {
  Serial.println(F("[GSM] Opening GPRS bearer..."));

  // Configure bearer profile 1 with APN
  gsmSerial.println("AT+SAPBR=3,1,\"Contype\",\"GPRS\"");
  _waitForResponse("OK");

  gsmSerial.print("AT+SAPBR=3,1,\"APN\",\"");
  gsmSerial.print(GSM_APN);
  gsmSerial.println("\"");
  _waitForResponse("OK");

  if (strlen(GSM_USER) > 0) {
    gsmSerial.print("AT+SAPBR=3,1,\"USER\",\"");
    gsmSerial.print(GSM_USER);
    gsmSerial.println("\"");
    _waitForResponse("OK");
  }

  if (strlen(GSM_PASS) > 0) {
    gsmSerial.print("AT+SAPBR=3,1,\"PWD\",\"");
    gsmSerial.print(GSM_PASS);
    gsmSerial.println("\"");
    _waitForResponse("OK");
  }

  // Open bearer
  gsmSerial.println("AT+SAPBR=1,1");
  if (!_waitForResponse("OK", 15000)) {
    Serial.println(F("[GSM] GPRS bearer open failed."));
    return false;
  }

  // Verify IP address assigned
  gsmSerial.println("AT+SAPBR=2,1");
  String ip_resp = _readResponse(3000);
  Serial.print(F("[GSM] IP: "));
  Serial.println(ip_resp);

  if (ip_resp.indexOf("0.0.0.0") >= 0) {
    Serial.println(F("[GSM] Invalid IP — GPRS failed."));
    return false;
  }

  Serial.println(F("[GSM] GPRS connected."));
  return true;
}

void gsm_gprs_disconnect() {
  gsmSerial.println("AT+SAPBR=0,1");
  _waitForResponse("OK", 5000);
  Serial.println(F("[GSM] GPRS bearer closed."));
}

/**
 * Upload JPEG image to cloud server using SIM800L HTTP AT commands.
 *
 * Flow:
 *   AT+HTTPINIT        — init HTTP service
 *   AT+HTTPPARA        — set URL and content type
 *   AT+HTTPDATA        — load data buffer with JPEG bytes
 *   AT+HTTPACTION=1    — execute POST
 *   AT+HTTPREAD        — read response
 *   AT+HTTPTERM        — terminate HTTP session
 */
bool gsm_http_post_image(const uint8_t* data, size_t length, const char* filename) {
  Serial.printf("[GSM] Uploading %zu bytes as '%s'...\n", length, filename);

  // Init HTTP
  gsmSerial.println("AT+HTTPINIT");
  if (!_waitForResponse("OK", 5000)) return false;

  // Set bearer profile
  gsmSerial.println("AT+HTTPPARA=\"CID\",1");
  _waitForResponse("OK");

  // Set URL
  gsmSerial.print("AT+HTTPPARA=\"URL\",\"http://");
  gsmSerial.print(SERVER_HOST);
  if (SERVER_PORT != 80) { gsmSerial.print(":"); gsmSerial.print(SERVER_PORT); }
  gsmSerial.print(SERVER_PATH);
  gsmSerial.println("\"");
  _waitForResponse("OK");

  // Set content type
  gsmSerial.println("AT+HTTPPARA=\"CONTENT\",\"image/jpeg\"");
  _waitForResponse("OK");

  // Load data into HTTP buffer
  // AT+HTTPDATA=<size>,<timeout_ms>
  gsmSerial.print("AT+HTTPDATA=");
  gsmSerial.print(length);
  gsmSerial.println(",10000");
  if (!_waitForResponse("DOWNLOAD", 5000)) {
    Serial.println(F("[GSM] HTTPDATA not ready."));
    gsmSerial.println("AT+HTTPTERM");
    return false;
  }

  // Send raw JPEG bytes
  gsmSerial.write(data, length);
  if (!_waitForResponse("OK", 15000)) {
    Serial.println(F("[GSM] HTTPDATA upload failed."));
    gsmSerial.println("AT+HTTPTERM");
    return false;
  }

  // Execute HTTP POST
  gsmSerial.println("AT+HTTPACTION=1");
  String action_resp = _readResponse(30000);  // wait up to 30s for server response
  Serial.print(F("[GSM] HTTP response: "));
  Serial.println(action_resp);

  bool success = (action_resp.indexOf(",200,") >= 0);

  // Read server response body (optional)
  gsmSerial.println("AT+HTTPREAD");
  Serial.println(_readResponse(3000));

  // Terminate HTTP session
  gsmSerial.println("AT+HTTPTERM");
  _waitForResponse("OK", 3000);

  if (success) {
    Serial.println(F("[GSM] ✅ Image uploaded successfully."));
  } else {
    Serial.println(F("[GSM] ❌ Upload failed — check server URL and connectivity."));
  }
  return success;
}

int gsm_signal_strength() {
  gsmSerial.println("AT+CSQ");
  String r = _readResponse(1000);
  int idx = r.indexOf("+CSQ: ");
  if (idx < 0) return 99;
  int rssi = r.substring(idx + 6).toInt();
  return rssi;
}

bool gsm_is_registered() {
  gsmSerial.println("AT+CREG?");
  String r = _readResponse(1000);
  return (r.indexOf(",1") >= 0 || r.indexOf(",5") >= 0);
}
