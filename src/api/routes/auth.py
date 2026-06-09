"""
CareFlow — Auth Routes: /auth/register, /auth/login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.schemas import DoctorCreate, DoctorOut, Token, LoginRequest
from src.models.models import Doctor
from src.auth.jwt import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=DoctorOut, status_code=201)
def register(doctor_in: DoctorCreate, db: Session = Depends(get_db)):
    """Register a new doctor / staff account."""
    if db.query(Doctor).filter(Doctor.email == doctor_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    doctor = Doctor(
        name=doctor_in.name,
        specialization=doctor_in.specialization,
        phone=doctor_in.phone,
        email=doctor_in.email,
        hashed_password=hash_password(doctor_in.password),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive a JWT bearer token."""
    doctor = db.query(Doctor).filter(Doctor.email == body.email).first()
    if not doctor or not verify_password(body.password, doctor.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(doctor.id), "name": doctor.name})
    return {"access_token": token, "token_type": "bearer"}
