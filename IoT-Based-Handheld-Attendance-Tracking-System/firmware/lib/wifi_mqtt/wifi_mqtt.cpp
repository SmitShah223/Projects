/**
 * wifi_mqtt.cpp — Wi-Fi + AWS IoT Core MQTT Implementation
 *
 * Dependencies (install via Arduino Library Manager):
 *   - WiFiClientSecure (built-in ESP32)
 *   - PubSubClient by Nick O'Leary
 *   - ArduinoJson by Benoit Blanchon
 *   - WiFi (built-in ESP32)
 *
 * Certificates: Store in SPIFFS at /certs/ca.pem, /certs/cert.pem, /certs/key.pem
 *               OR embed directly as string literals in secrets.h (not committed to git)
 */

#include "wifi_mqtt.h"
#include "local_storage.h"
#include "secrets.h"          // AWS_IOT_ENDPOINT, WIFI_SSID, WIFI_PASS, certs

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

// ─── MQTT Topics ─────────────────────────────────────────────────────────────
#define TOPIC_ATT_LOG    "attendance/log"
#define TOPIC_ATT_SYNC   "attendance/sync"
#define TOPIC_STU_REG    "student/register"
#define TOPIC_ATT_ACK    "attendance/ack"

static WiFiClientSecure wifiClient;
static PubSubClient     mqttClient(wifiClient);

// ─── MQTT Callback ────────────────────────────────────────────────────────────
static void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.println("[MQTT] Received on " + String(topic) + ": " + msg);

  if (strcmp(topic, TOPIC_STU_REG) == 0) {
    // Parse and cache new student UID mapping
    StaticJsonDocument<256> doc;
    deserializeJson(doc, msg);
    int    id  = doc["student_id"];
    String uid = doc["picc_uid"].as<String>();
    storage_cacheStudent(id, uid);
    Serial.printf("[MQTT] Cached student ID=%d  UID=%s\n", id, uid.c_str());
  }

  if (strcmp(topic, TOPIC_ATT_ACK) == 0) {
    StaticJsonDocument<128> doc;
    deserializeJson(doc, msg);
    int logID = doc["log_id"];
    storage_markSynced(logID);
  }
}

// ─── Wi-Fi ────────────────────────────────────────────────────────────────────
static void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500); Serial.print('.'); retries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected. IP: " + WiFi.localIP().toString());
    // Sync NTP time
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  } else {
    Serial.println(F("\n[WiFi] Connection failed — running offline."));
  }
}

// ─── MQTT ─────────────────────────────────────────────────────────────────────
static void connectMQTT() {
  wifiClient.setCACert(AWS_CERT_CA);
  wifiClient.setCertificate(AWS_CERT_CRT);
  wifiClient.setPrivateKey(AWS_CERT_PRIVATE);

  mqttClient.setServer(AWS_IOT_ENDPOINT, 8883);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(2048);

  String clientID = "ESP32-" + WiFi.macAddress();
  if (mqttClient.connect(clientID.c_str())) {
    Serial.println(F("[MQTT] Connected to AWS IoT Core."));
    mqttClient.subscribe(TOPIC_STU_REG);
    mqttClient.subscribe(TOPIC_ATT_ACK);
  } else {
    Serial.printf("[MQTT] Connection failed, state=%d\n", mqttClient.state());
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────
void wifi_mqtt_init() {
  connectWiFi();
  if (WiFi.status() == WL_CONNECTED) connectMQTT();
}

void wifi_mqtt_loop() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();
}

bool wifi_isConnected() {
  return WiFi.status() == WL_CONNECTED && mqttClient.connected();
}

void mqtt_publishAttendance(int studentID, const String& uid, const String& timestamp) {
  StaticJsonDocument<256> doc;
  doc["student_id"] = studentID;
  doc["picc_uid"]   = uid;
  doc["timestamp"]  = timestamp;
  doc["device_id"]  = WiFi.macAddress();

  char buf[256];
  serializeJson(doc, buf);
  bool ok = mqttClient.publish(TOPIC_ATT_LOG, buf);
  Serial.println(ok ? "[MQTT] Attendance published." : "[MQTT] Publish failed — queued locally.");
}

void mqtt_syncPendingRecords() {
  // Load all unsynced records from SPIFFS and publish them
  int count = storage_getPendingCount();
  if (count == 0) return;
  Serial.printf("[MQTT] Syncing %d pending record(s)…\n", count);

  for (int i = 0; i < count; i++) {
    AttendanceRecord rec = storage_getPendingRecord(i);
    mqtt_publishAttendance(rec.studentID, rec.uid, rec.timestamp);
    delay(100);  // rate-limit
  }
}

String get_timestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "1970-01-01T00:00:00Z";
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}
