"""
main.py — FastAPI application entry point.

Starts the server, creates DB tables, and boots the MQTT listener.
Run with:   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.api import attendance, students
from app.dependencies.mqtt import init_mqtt

# ─── Create tables ────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "IoT Attendance System API",
    description = "Cloud backend for the IoT-Based Handheld Attendance Tracking System.\n"
                  "Published at ICCDS February 2024 (ISBN: 979-8-9879839-7-3)",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(attendance.router)
app.include_router(students.router)

# ─── Events ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_mqtt()
    print("[APP] Server started. MQTT listener active.")

@app.get("/health")
def health():
    return {"status": "ok", "service": "IoT Attendance System"}
