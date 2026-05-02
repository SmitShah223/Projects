"""
db/schemas.py — Pydantic schemas for request/response serialisation.
"""
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional
from app.db.models import AttStatus, WifiStatus


# ─── Student ─────────────────────────────────────────────────────────────────
class StudentBase(BaseModel):
    fname: str
    lname: str
    picc_uid: str

class StudentCreate(StudentBase):
    student_uid: Optional[str] = None

class StudentOut(StudentBase):
    id: int
    student_uid: Optional[str]
    class Config: from_attributes = True


# ─── Subject ─────────────────────────────────────────────────────────────────
class SubjectOut(BaseModel):
    id: int
    subj_name: str
    subj_category: Optional[int]
    class Config: from_attributes = True


# ─── Schedule ────────────────────────────────────────────────────────────────
class ScheduleOut(BaseModel):
    id: int
    lecture_id: int
    date: date
    start_time: time
    end_time: time
    class Config: from_attributes = True


# ─── Attendance Log ───────────────────────────────────────────────────────────
class AttendanceLogBase(BaseModel):
    schedule_id: int
    lecture_id:  int
    student_id:  int
    device_id:   Optional[int] = None
    att_status:  AttStatus = AttStatus.PRESENT

class AttendanceLogCreate(AttendanceLogBase):
    pass

class AttendanceLogOut(AttendanceLogBase):
    id:        int
    timestamp: datetime
    class Config: from_attributes = True


# ─── MQTT Attendance Payload (from ESP32) ────────────────────────────────────
class MQTTAttendancePayload(BaseModel):
    student_id: int
    picc_uid:   str
    timestamp:  str
    device_id:  Optional[str] = None   # MAC address of device


# ─── Device ───────────────────────────────────────────────────────────────────
class DeviceOut(BaseModel):
    id:               int
    hw_uuid:          str
    wifi_status:      WifiStatus
    battery_status:   Optional[float]
    last_update_time: datetime
    class Config: from_attributes = True
