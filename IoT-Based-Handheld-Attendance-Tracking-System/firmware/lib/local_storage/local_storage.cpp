/**
 * local_storage.cpp — SPIFFS-based Offline Storage Implementation
 * Dependency: SPIFFS (built-in ESP32 core), ArduinoJson
 */

#include "local_storage.h"
#include <SPIFFS.h>
#include <ArduinoJson.h>

#define STUDENTS_FILE "/students.json"
#define LOG_FILE      "/log.json"

// ─── Init ─────────────────────────────────────────────────────────────────────
void storage_init() {
  if (!SPIFFS.begin(true)) {
    Serial.println(F("[STOR] SPIFFS mount failed!"));
    return;
  }
  Serial.println(F("[STOR] SPIFFS mounted."));

  // Create empty files if they don't exist
  if (!SPIFFS.exists(STUDENTS_FILE)) {
    File f = SPIFFS.open(STUDENTS_FILE, "w");
    f.println("[]");
    f.close();
  }
  if (!SPIFFS.exists(LOG_FILE)) {
    File f = SPIFFS.open(LOG_FILE, "w");
    f.println("[]");
    f.close();
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
static DynamicJsonDocument _readJSON(const char* path, size_t capacity = 4096) {
  DynamicJsonDocument doc(capacity);
  File f = SPIFFS.open(path, "r");
  if (f) { deserializeJson(doc, f); f.close(); }
  return doc;
}

static void _writeJSON(const char* path, DynamicJsonDocument& doc) {
  File f = SPIFFS.open(path, "w");
  if (f) { serializeJson(doc, f); f.close(); }
}

// ─── Student Cache ─────────────────────────────────────────────────────────────
int storage_lookupUID(const String& uid) {
  DynamicJsonDocument doc = _readJSON(STUDENTS_FILE);
  for (JsonObject s : doc.as<JsonArray>()) {
    if (s["uid"].as<String>() == uid)
      return s["student_id"].as<int>();
  }
  return -1;
}

void storage_cacheStudent(int id, const String& uid) {
  DynamicJsonDocument doc = _readJSON(STUDENTS_FILE);
  JsonArray arr = doc.as<JsonArray>();

  // Update if exists, otherwise append
  for (JsonObject s : arr) {
    if (s["student_id"].as<int>() == id) {
      s["uid"] = uid;
      _writeJSON(STUDENTS_FILE, doc);
      return;
    }
  }
  JsonObject s  = arr.createNestedObject();
  s["student_id"] = id;
  s["uid"]        = uid;
  _writeJSON(STUDENTS_FILE, doc);
  Serial.printf("[STOR] Cached student ID=%d UID=%s\n", id, uid.c_str());
}

// ─── Attendance Log ────────────────────────────────────────────────────────────
void storage_logAttendance(int studentID, const String& uid, const String& timestamp) {
  DynamicJsonDocument doc = _readJSON(LOG_FILE, 8192);
  JsonArray arr = doc.as<JsonArray>();

  JsonObject rec    = arr.createNestedObject();
  int logID         = arr.size();      // simple sequential ID
  rec["log_id"]     = logID;
  rec["student_id"] = studentID;
  rec["uid"]        = uid;
  rec["timestamp"]  = timestamp;
  rec["synced"]     = false;

  _writeJSON(LOG_FILE, doc);
  Serial.printf("[STOR] Logged attendance record %d\n", logID);
}

void storage_markSynced(int logID) {
  DynamicJsonDocument doc = _readJSON(LOG_FILE, 8192);
  for (JsonObject r : doc.as<JsonArray>()) {
    if (r["log_id"].as<int>() == logID) {
      r["synced"] = true;
      break;
    }
  }
  _writeJSON(LOG_FILE, doc);
}

int storage_getPendingCount() {
  DynamicJsonDocument doc = _readJSON(LOG_FILE, 8192);
  int count = 0;
  for (JsonObject r : doc.as<JsonArray>()) {
    if (!r["synced"].as<bool>()) count++;
  }
  return count;
}

AttendanceRecord storage_getPendingRecord(int index) {
  DynamicJsonDocument doc = _readJSON(LOG_FILE, 8192);
  int found = 0;
  for (JsonObject r : doc.as<JsonArray>()) {
    if (!r["synced"].as<bool>()) {
      if (found == index) {
        return {
          r["log_id"].as<int>(),
          r["student_id"].as<int>(),
          r["uid"].as<String>(),
          r["timestamp"].as<String>(),
          false
        };
      }
      found++;
    }
  }
  return {-1, -1, "", "", false};
}
