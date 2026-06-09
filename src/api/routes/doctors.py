"""
CareFlow — Doctor / Staff Routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.schemas import DoctorOut
from src.models.models import Doctor
from src.auth.jwt import get_current_doctor

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=List[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """Public — used in the booking form doctor dropdown."""
    return db.query(Doctor).filter(Doctor.is_active == True).all()


@router.get("/me", response_model=DoctorOut)
def get_me(current: Doctor = Depends(get_current_doctor)):
    """Get the currently authenticated doctor's profile."""
    return current


@router.delete("/{doctor_id}", status_code=204)
def deactivate_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current: Doctor = Depends(get_current_doctor),
):
    """Deactivate a doctor account (soft delete)."""
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(404, "Doctor not found")
    doc.is_active = False
    db.commit()
