"""
api/students.py — Student CRUD endpoints.

GET    /students/          — list all students
GET    /students/{id}      — get student by ID
POST   /students/          — register new student (admin)
DELETE /students/{id}      — remove student (admin)
POST   /students/register-device — push student UID mapping to device via MQTT
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models, schemas
from app.dependencies.authentication import require_admin
from app.dependencies.mqtt import get_mqtt_client

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", response_model=List[schemas.StudentOut])
def list_students(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    return db.query(models.Student).offset(skip).limit(limit).all()


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s


@router.post("/", response_model=schemas.StudentOut, status_code=201)
def create_student(
    payload: schemas.StudentCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    # Check for duplicate picc_uid
    existing = db.query(models.Student).filter(
        models.Student.picc_uid == payload.picc_uid
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="RFID card already registered.")

    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(s)
    db.commit()


@router.post("/register-device")
def push_student_to_device(
    student_id: int,
    db: Session = Depends(get_db),
    mqtt=Depends(get_mqtt_client),
    _: str = Depends(require_admin),
):
    """
    Push student UID mapping to all subscribed ESP32 devices via MQTT topic:
      student/register  →  { "student_id": X, "picc_uid": "XXXXXXXX" }
    The ESP32 caches this locally for offline operation.
    """
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    import json
    payload = json.dumps({"student_id": s.id, "picc_uid": s.picc_uid})
    mqtt.publish("student/register", payload, qos=1)
    return {"status": "pushed", "student_id": s.id, "picc_uid": s.picc_uid}
