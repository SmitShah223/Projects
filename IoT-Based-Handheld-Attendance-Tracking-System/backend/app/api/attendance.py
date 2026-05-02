"""
api/attendance.py — Attendance endpoints.

GET  /attendance/             — list all attendance records (admin)
GET  /attendance/student/{id} — records for a specific student
POST /attendance/             — manually log attendance (for testing)
GET  /attendance/analytics    — summary statistics for data visualisation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date

from app.db.database import get_db
from app.db import models, schemas
from app.dependencies.authentication import require_admin

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/", response_model=List[schemas.AttendanceLogOut])
def list_attendance(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    return db.query(models.AttendanceLog).offset(skip).limit(limit).all()


@router.get("/student/{student_id}", response_model=List[schemas.AttendanceLogOut])
def get_student_attendance(student_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(models.AttendanceLog)
        .filter(models.AttendanceLog.student_id == student_id)
        .order_by(models.AttendanceLog.timestamp.desc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="No records found for this student.")
    return records


@router.post("/", response_model=schemas.AttendanceLogOut, status_code=201)
def create_attendance(
    payload: schemas.AttendanceLogCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    record = models.AttendanceLog(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/analytics")
def attendance_analytics(
    from_date: date = None,
    to_date:   date = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Return aggregate attendance statistics for dashboard visualisation.
    Response includes:
      - total_records
      - present_count / absent_count / late_count
      - per-student attendance percentage
      - per-day record counts
    """
    q = db.query(models.AttendanceLog)
    if from_date:
        q = q.filter(func.date(models.AttendanceLog.timestamp) >= from_date)
    if to_date:
        q = q.filter(func.date(models.AttendanceLog.timestamp) <= to_date)

    total   = q.count()
    present = q.filter(models.AttendanceLog.att_status == "PRESENT").count()
    absent  = q.filter(models.AttendanceLog.att_status == "ABSENT").count()
    late    = q.filter(models.AttendanceLog.att_status == "LATE").count()

    # Per-student attendance percentage
    student_stats = (
        db.query(
            models.Student.fname,
            models.Student.lname,
            func.count(models.AttendanceLog.id).label("total"),
            func.sum(
                (models.AttendanceLog.att_status == "PRESENT").cast(models.Integer)
            ).label("present"),
        )
        .join(models.AttendanceLog, models.Student.id == models.AttendanceLog.student_id)
        .group_by(models.Student.id)
        .all()
    )

    students_out = [
        {
            "name": f"{s.fname} {s.lname}",
            "total": s.total,
            "present": s.present or 0,
            "percentage": round((s.present or 0) / s.total * 100, 1) if s.total else 0,
        }
        for s in student_stats
    ]

    return {
        "total_records": total,
        "present_count": present,
        "absent_count":  absent,
        "late_count":    late,
        "students":      students_out,
    }
