"""
db/models.py — SQLAlchemy ORM models matching the database schema shown
               in the project report (Fig. 4).

Tables:
    Subject       → academic subjects
    Teacher       → teaching staff
    Lecture       → scheduled lectures (subject + teacher + time)
    Schedule      → specific occurrence of a lecture
    Student       → enrolled students (with picc_uid for RFID card)
    Device        → registered ESP32 devices
    AttendanceLog → final attendance records per student per schedule
    AuthLog       → raw authentication attempts (RFID + FP events)
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Enum, DateTime, Date, Time,
    Float, Boolean, ForeignKey, func
)
from sqlalchemy.orm import relationship
from .database import Base
import enum

# ─── Enums ────────────────────────────────────────────────────────────────────
class AttStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT  = "ABSENT"
    LATE    = "LATE"

class WifiStatus(str, enum.Enum):
    ONLINE  = "ONLINE"
    OFFLINE = "OFFLINE"

# ─── Subject ──────────────────────────────────────────────────────────────────
class Subject(Base):
    __tablename__ = "subject"
    id            = Column(BigInteger, primary_key=True, index=True)
    subj_name     = Column(String(100), nullable=False)
    subj_category = Column(BigInteger)
    lectures      = relationship("Lecture", back_populates="subject")

# ─── Teacher ──────────────────────────────────────────────────────────────────
class Teacher(Base):
    __tablename__ = "teacher"
    id            = Column(BigInteger, primary_key=True, index=True)
    fname         = Column(String(50), nullable=False)
    lname         = Column(String(50), nullable=False)
    teacher_uid   = Column(String(64), unique=True)   # fingerprint/RFID uid
    picc_uid      = Column(String(32), unique=True)   # RFID card UID
    lectures      = relationship("Lecture", back_populates="teacher")
    auth_logs     = relationship("AuthLog", back_populates="teacher")

# ─── Lecture ──────────────────────────────────────────────────────────────────
class Lecture(Base):
    __tablename__ = "lecture"
    id            = Column(BigInteger, primary_key=True, index=True)
    teacher_id    = Column(BigInteger, ForeignKey("teacher.id"), nullable=False)
    subject_id    = Column(BigInteger, ForeignKey("subject.id"), nullable=False)
    teacher       = relationship("Teacher", back_populates="lectures")
    subject       = relationship("Subject", back_populates="lectures")
    schedules     = relationship("Schedule", back_populates="lecture")

# ─── Schedule ─────────────────────────────────────────────────────────────────
class Schedule(Base):
    __tablename__  = "schedule"
    id             = Column(BigInteger, primary_key=True, index=True)
    lecture_id     = Column(BigInteger, ForeignKey("lecture.id"), nullable=False)
    date           = Column(Date, nullable=False)
    start_time     = Column(Time, nullable=False)
    end_time       = Column(Time, nullable=False)
    lecture        = relationship("Lecture", back_populates="schedules")
    attendance_log = relationship("AttendanceLog", back_populates="schedule")
    auth_logs      = relationship("AuthLog", back_populates="schedule")

# ─── Student ──────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__  = "student"
    id             = Column(BigInteger, primary_key=True, index=True)
    fname          = Column(String(50), nullable=False)
    lname          = Column(String(50), nullable=False)
    student_uid    = Column(String(64), unique=True)   # fingerprint template ID
    picc_uid       = Column(String(32), unique=True, nullable=False)  # RFID card UID
    attendance_log = relationship("AttendanceLog", back_populates="student")

# ─── Device ───────────────────────────────────────────────────────────────────
class Device(Base):
    __tablename__    = "device"
    id               = Column(BigInteger, primary_key=True, index=True)
    hw_uuid          = Column(String(36), unique=True, nullable=False)  # ESP32 MAC
    teacher_id       = Column(BigInteger, ForeignKey("teacher.id"))
    wifi_status      = Column(Enum(WifiStatus), default=WifiStatus.OFFLINE)
    battery_status   = Column(Float)
    last_update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    attendance_log   = relationship("AttendanceLog", back_populates="device")

# ─── AttendanceLog ────────────────────────────────────────────────────────────
class AttendanceLog(Base):
    __tablename__ = "attendance_log"
    id            = Column(BigInteger, primary_key=True, index=True)
    schedule_id   = Column(BigInteger, ForeignKey("schedule.id"), nullable=False)
    lecture_id    = Column(BigInteger, ForeignKey("lecture.id"),  nullable=False)
    student_id    = Column(BigInteger, ForeignKey("student.id"),  nullable=False)
    device_id     = Column(BigInteger, ForeignKey("device.id"))
    att_status    = Column(Enum(AttStatus), default=AttStatus.PRESENT)
    timestamp     = Column(DateTime, server_default=func.now())
    schedule      = relationship("Schedule", back_populates="attendance_log")
    student       = relationship("Student",  back_populates="attendance_log")
    device        = relationship("Device",   back_populates="attendance_log")

# ─── AuthLog ──────────────────────────────────────────────────────────────────
class AuthLog(Base):
    __tablename__ = "auth_log"
    id            = Column(BigInteger, primary_key=True, index=True)
    teacher_id    = Column(BigInteger, ForeignKey("teacher.id"))
    lecture_id    = Column(BigInteger, ForeignKey("lecture.id"))
    device_id     = Column(BigInteger, ForeignKey("device.id"))
    timestamp     = Column(DateTime, server_default=func.now())
    teacher       = relationship("Teacher",  back_populates="auth_logs")
    schedule      = relationship("Schedule", back_populates="auth_logs")
