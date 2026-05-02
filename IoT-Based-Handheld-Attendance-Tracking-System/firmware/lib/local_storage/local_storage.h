/**
 * local_storage.h — SPIFFS-based Offline Storage Interface
 *
 * Stores two things on ESP32 SPIFFS (flash filesystem):
 *   /students.json    — cached UID → studentID mappings from cloud
 *   /log.json         — attendance records, with sync status flag
 */

#pragma once
#include <Arduino.h>

struct AttendanceRecord {
  int    logID;
  int    studentID;
  String uid;
  String timestamp;
  bool   synced;
};

void             storage_init();
int              storage_lookupUID(const String& uid);     // returns studentID or -1
void             storage_cacheStudent(int id, const String& uid);
void             storage_logAttendance(int studentID, const String& uid, const String& timestamp);
void             storage_markSynced(int logID);
int              storage_getPendingCount();
AttendanceRecord storage_getPendingRecord(int index);
