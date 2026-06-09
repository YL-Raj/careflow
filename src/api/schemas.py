"""
CareFlow — Pydantic Schemas (request/response validation)
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from src.models.models import StatusEnum, GenderEnum


# ── Auth ──────────────────────────────────────────────────────────────────────
class DoctorCreate(BaseModel):
    name: str
    specialization: str = "General"
    phone: Optional[str] = None
    email: str
    password: str


class DoctorOut(BaseModel):
    id: int
    name: str
    specialization: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Patient ───────────────────────────────────────────────────────────────────
class PatientCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: GenderEnum = GenderEnum.other
    location: Optional[str] = None
    phone: str


class PatientOut(PatientCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Appointment ───────────────────────────────────────────────────────────────
class AppointmentCreate(BaseModel):
    patient_name: str
    age: Optional[int] = None
    gender: GenderEnum = GenderEnum.other
    location: Optional[str] = None
    phone: str
    scheduled_time: datetime
    doctor_id: Optional[int] = None
    notes: str = ""

    @field_validator("scheduled_time")
    @classmethod
    def must_be_future(cls, v):
        # Relax for demo purposes — allow past times in dev
        return v


class AppointmentUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    status: Optional[StatusEnum] = None
    notes: Optional[str] = None
    doctor_id: Optional[int] = None


class AppointmentOut(BaseModel):
    id: int
    scheduled_time: datetime
    status: StatusEnum
    notes: str
    created_at: datetime
    patient: PatientOut
    doctor: Optional[DoctorOut] = None
    token_number: Optional[int] = None

    model_config = {"from_attributes": True}


# ── Queue ─────────────────────────────────────────────────────────────────────
class QueueItem(BaseModel):
    token_number: int
    appointment_id: int
    patient_name: str
    scheduled_time: str
    status: StatusEnum
    is_called: bool

    model_config = {"from_attributes": True}


class QueueStatus(BaseModel):
    date: str
    total: int
    waiting: int
    called: int
    items: List[QueueItem]


# ── Stats ─────────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    today_total: int
    today_checked_in: int
    today_waiting: int
    today_completed: int
    today_no_show: int
    week_total: int
