/**
 * wifi_mqtt.h — Wi-Fi + AWS IoT Core MQTT Interface
 *
 * Uses TLS/SSL to connect to AWS IoT Core endpoint.
 * Certificates must be placed in firmware/certs/ (not committed to git).
 *
 * Topics:
 *   Publish  : attendance/log        — new attendance record
 *   Publish  : attendance/sync       — batch sync of offline records
 *   Subscribe: student/register      — receive new student UID→ID mappings from cloud
 *   Subscribe: attendance/ack        — cloud acknowledgement of received record
 */

#pragma once
#include <Arduino.h>

void   wifi_mqtt_init();
void   wifi_mqtt_loop();
bool   wifi_isConnected();

void   mqtt_publishAttendance(int studentID, const String& uid, const String& timestamp);
void   mqtt_syncPendingRecords();

/** Returns current time as ISO-8601 string via NTP (e.g. "2024-02-10T09:30:00Z"). */
String get_timestamp();
