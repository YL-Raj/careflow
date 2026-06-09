"""
CareFlow — Queue Routes
Upgraded from original display.py (Tkinter + pyttsx3 TTS queue announcer).
Now a REST API that drives any frontend display — React kiosk, TV, mobile.
"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from src.api.database import get_db
from src.api.schemas import QueueStatus, QueueItem, DashboardStats
from src.models.models import QueueToken, Appointment, StatusEnum
from src.auth.jwt import get_current_doctor
from src.models.models import Doctor

router = APIRouter(prefix="/queue", tags=["Queue Management"])


@router.get("/today", response_model=QueueStatus)
def get_today_queue(
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """
    Full queue status for today.
    Replaces original display.py patient list — now API-driven for any display device.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    tokens = (
        db.query(QueueToken)
        .filter(QueueToken.date == today_str)
        .options(joinedload(QueueToken.appointment).joinedload(Appointment.patient))
        .order_by(QueueToken.token_number)
        .all()
    )

    items = []
    for t in tokens:
        appt = t.appointment
        items.append(QueueItem(
            token_number=t.token_number,
            appointment_id=appt.id,
            patient_name=appt.patient.name,
            scheduled_time=appt.scheduled_time.strftime("%H:%M"),
            status=appt.status,
            is_called=t.is_called,
        ))

    waiting = sum(1 for i in items if not i.is_called and i.status == StatusEnum.scheduled)
    called = sum(1 for i in items if i.is_called)

    return QueueStatus(
        date=today_str,
        total=len(items),
        waiting=waiting,
        called=called,
        items=items,
    )


@router.post("/{token_number}/call", response_model=QueueItem)
def call_token(
    token_number: int,
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """
    Mark a token as called (Next Patient).
    Replaces original display.py 'Next Patient' button + pyttsx3 TTS.
    Frontend should trigger their own TTS or announcement sound on this event.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    token = (
        db.query(QueueToken)
        .filter(QueueToken.token_number == token_number, QueueToken.date == today_str)
        .options(joinedload(QueueToken.appointment).joinedload(Appointment.patient))
        .first()
    )
    if not token:
        raise HTTPException(404, f"Token {token_number} not found for today")

    token.is_called = True
    token.called_at = datetime.utcnow()
    token.appointment.status = StatusEnum.checked_in
    db.commit()
    db.refresh(token)

    return QueueItem(
        token_number=token.token_number,
        appointment_id=token.appointment.id,
        patient_name=token.appointment.patient.name,
        scheduled_time=token.appointment.scheduled_time.strftime("%H:%M"),
        status=token.appointment.status,
        is_called=token.is_called,
    )


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: Doctor = Depends(get_current_doctor),
):
    """Dashboard summary stats for today + this week."""
    today = date.today()
    today_start = datetime(today.year, today.month, today.day)
    today_end = datetime(today.year, today.month, today.day, 23, 59, 59)

    from sqlalchemy import func
    today_appts = (
        db.query(Appointment)
        .filter(Appointment.scheduled_time.between(today_start, today_end))
        .all()
    )
    from datetime import timedelta
    week_start = today_start - timedelta(days=today.weekday())
    week_count = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.scheduled_time >= week_start)
        .scalar()
    )

    return DashboardStats(
        today_total=len(today_appts),
        today_checked_in=sum(1 for a in today_appts if a.status == StatusEnum.checked_in),
        today_waiting=sum(1 for a in today_appts if a.status == StatusEnum.scheduled),
        today_completed=sum(1 for a in today_appts if a.status == StatusEnum.completed),
        today_no_show=sum(1 for a in today_appts if a.status == StatusEnum.no_show),
        week_total=week_count or 0,
    )
