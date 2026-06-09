"""
CareFlow — SQLAlchemy Models
Migrated and modernised from the original SQLite schema in database.db:
  appointments(ID, name, age, gender, location, phone, scheduled_time)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from src.api.database import Base


class StatusEnum(str, enum.Enum):
    scheduled = "scheduled"
    checked_in = "checked_in"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialization = Column(String, default="General")
    phone = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="doctor")
    tokens = relationship("QueueToken", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    # Mirrors original: name, age, gender, location, phone
    name = Column(String, nullable=False, index=True)
    age = Column(Integer)
    gender = Column(Enum(GenderEnum), default=GenderEnum.other)
    location = Column(String)
    phone = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    # Mirrors original: scheduled_time
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.scheduled)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    token = relationship("QueueToken", back_populates="appointment", uselist=False)


class QueueToken(Base):
    __tablename__ = "queue_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_number = Column(Integer, nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    is_called = Column(Boolean, default=False)
    called_at = Column(DateTime, nullable=True)

    appointment = relationship("Appointment", back_populates="token")
    doctor = relationship("Doctor", back_populates="tokens")
