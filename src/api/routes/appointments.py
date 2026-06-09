"""
CareFlow — Appointment Routes
Full CRUD upgraded from original Tkinter forms (appointment.py / update.py).
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.api.database import get_db
from src.api.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from src.models.models import Appointment, Patient, QueueToken, StatusEnum
from src.auth.jwt import get_current_doctor
from src.models.models import Doctor

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _get_or_create_patient(db: Session, name: str, age, gender, location, phone) -> Patient:
    """Find patient by phone or create a new one."""
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if not patient:
        patient = Patient(name=name, age=age, gender=gender, location=location, phone=phone)
        db.add(patient)
        db.flush()
    return patient


def _assign_token(db: Session, appointment: Appointment) -> int:
    """Assign the next sequential token number for the appointment date."""
    appt_date = appointment.scheduled_time.strftime("%Y-%m-%d")
    last_token = (
        db.query(QueueToken)
        .filter(QueueToken.date == appt_date, QueueToken.doctor_id == appointment.doctor_id)
        .order_by(QueueToken.token_number.desc())
        .first()
    )
    next_num = (last_token.token_number + 1) if last_token else 1
    token = QueueToken(
        token_number=next_num,
        appointment_id=appointment.id,
        doctor_id=appointment.doctor_id,
        date=appt_date,
    )
    db.add(token)
    db.flush()
    return next_num


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db)):
    """
    Book a new appointment.
    Mirrors original add_appointment() from appointment.py.
    No auth required — patients book directly.
    """
    patient = _get_or_create_patient(
        db, body.patient_name, body.age, body.gender, body.location, body.phone
    )
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=body.doctor_id,
        scheduled_time=body.scheduled_time,
        notes=body.notes,
    )
    db.add(appt)
    db.flush()
    token_num = _assign_token(db, appt)
    db.commit()
    db.refresh(appt)
    appt.token_number = token_num
    return _build_out(appt, db)


@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    date_filter: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    status: Optional[StatusEnum] = None,
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """List all appointments. Optionally filter by date or status. Requires auth."""
    q = db.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.doctor),
        joinedload(Appointment.token),
    )
    if date_filter:
        try:
            d = datetime.strptime(date_filter, "%Y-%m-%d")
            q = q.filter(
                Appointment.scheduled_time >= d,
                Appointment.scheduled_time < datetime(d.year, d.month, d.day, 23, 59, 59),
            )
        except ValueError:
            raise HTTPException(400, "date_filter must be YYYY-MM-DD")
    if status:
        q = q.filter(Appointment.status == status)
    appts = q.order_by(Appointment.scheduled_time).all()
    return [_build_out(a, db) for a in appts]


@router.get("/today", response_model=List[AppointmentOut])
def today_appointments(db: Session = Depends(get_db), _: Doctor = Depends(get_current_doctor)):
    """Shortcut: today's appointment list for the reception desk."""
    today = date.today()
    appts = (
        db.query(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.doctor), joinedload(Appointment.token))
        .filter(
            Appointment.scheduled_time >= datetime(today.year, today.month, today.day),
            Appointment.scheduled_time < datetime(today.year, today.month, today.day, 23, 59, 59),
        )
        .order_by(Appointment.scheduled_time)
        .all()
    )
    return [_build_out(a, db) for a in appts]


@router.get("/{appt_id}", response_model=AppointmentOut)
def get_appointment(appt_id: int, db: Session = Depends(get_db)):
    """Get a single appointment by ID (public — for patient self-service)."""
    appt = _fetch_or_404(appt_id, db)
    return _build_out(appt, db)


@router.put("/{appt_id}", response_model=AppointmentOut)
def update_appointment(
    appt_id: int,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """
    Update appointment status, time, or notes.
    Mirrors original update_db() from update.py.
    """
    appt = _fetch_or_404(appt_id, db)
    if body.scheduled_time:
        appt.scheduled_time = body.scheduled_time
    if body.status:
        appt.status = body.status
    if body.notes is not None:
        appt.notes = body.notes
    if body.doctor_id is not None:
        appt.doctor_id = body.doctor_id
    db.commit()
    db.refresh(appt)
    return _build_out(appt, db)


@router.delete("/{appt_id}", status_code=204)
def cancel_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """
    Cancel (soft-delete) an appointment.
    Mirrors original delete_db() from update.py.
    """
    appt = _fetch_or_404(appt_id, db)
    appt.status = StatusEnum.cancelled
    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fetch_or_404(appt_id: int, db: Session) -> Appointment:
    appt = (
        db.query(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.doctor), joinedload(Appointment.token))
        .filter(Appointment.id == appt_id)
        .first()
    )
    if not appt:
        raise HTTPException(404, "Appointment not found")
    return appt


def _build_out(appt: Appointment, db: Session) -> AppointmentOut:
    token_num = appt.token.token_number if appt.token else None
    return AppointmentOut(
        id=appt.id,
        scheduled_time=appt.scheduled_time,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        patient=appt.patient,
        doctor=appt.doctor,
        token_number=token_num,
    )
