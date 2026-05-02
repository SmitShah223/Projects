"""
dependencies/mqtt.py — AWS IoT Core MQTT listener (server-side).

Subscribes to:
  attendance/log   — new records from devices
  attendance/sync  — bulk offline sync batches

On receipt → validates student → writes AttendanceLog → acknowledges device.
"""
import json
import threading
from datetime import datetime
from awscrt import mqtt
from awsiot import mqtt_connection_builder

from app.config.settings import settings
from app.db.database import SessionLocal
from app.db import models

_mqtt_connection = None


def _on_attendance_log(topic, payload, **kwargs):
    """Callback: process a single attendance record from a device."""
    try:
        data = json.loads(payload.decode())
        student_id = data.get("student_id")
        picc_uid   = data.get("picc_uid")
        timestamp  = data.get("timestamp", datetime.utcnow().isoformat())
        device_mac = data.get("device_id")

        db = SessionLocal()
        try:
            student = db.query(models.Student).filter(
                models.Student.id == student_id,
                models.Student.picc_uid == picc_uid,
            ).first()

            if not student:
                print(f"[MQTT] Unknown student_id={student_id} uid={picc_uid}")
                return

            # Find the active schedule for this lecture time
            # (simplified: use the most recent schedule)
            schedule = (
                db.query(models.Schedule)
                .order_by(models.Schedule.date.desc())
                .first()
            )

            log = models.AttendanceLog(
                schedule_id = schedule.id if schedule else None,
                lecture_id  = schedule.lecture_id if schedule else None,
                student_id  = student.id,
                att_status  = models.AttStatus.PRESENT,
                timestamp   = datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            # Acknowledge to device
            ack_payload = json.dumps({"log_id": data.get("log_id", 0), "status": "ok"})
            _mqtt_connection.publish(
                topic   = "attendance/ack",
                payload = ack_payload,
                qos     = mqtt.QoS.AT_LEAST_ONCE,
            )
            print(f"[MQTT] Attendance logged: student={student_id} time={timestamp}")

        finally:
            db.close()

    except Exception as e:
        print(f"[MQTT] Error processing attendance: {e}")


def _start_listener():
    global _mqtt_connection
    _mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint             = settings.aws_iot_endpoint,
        cert_filepath        = settings.iot_cert_path,
        pri_key_filepath     = settings.iot_key_path,
        ca_filepath          = settings.iot_ca_path,
        client_id            = "attendance-server",
        clean_session        = False,
        keep_alive_secs      = 30,
    )
    connect_future = _mqtt_connection.connect()
    connect_future.result()
    print("[MQTT] Server connected to AWS IoT Core.")

    _mqtt_connection.subscribe(
        topic    = "attendance/log",
        qos      = mqtt.QoS.AT_LEAST_ONCE,
        callback = _on_attendance_log,
    )
    _mqtt_connection.subscribe(
        topic    = "attendance/sync",
        qos      = mqtt.QoS.AT_LEAST_ONCE,
        callback = _on_attendance_log,   # same handler for bulk sync
    )
    print("[MQTT] Subscribed to attendance/log and attendance/sync")


def init_mqtt():
    t = threading.Thread(target=_start_listener, daemon=True)
    t.start()


def get_mqtt_client():
    """FastAPI dependency — returns the active MQTT connection."""
    return _mqtt_connection
