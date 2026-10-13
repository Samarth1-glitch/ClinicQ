"""SQLAlchemy ORM models for ClinicQ."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

BOOKED = "booked"
CHECKED_IN = "checked_in"
COMPLETED = "completed"
CANCELLED = "cancelled"

# status -> statuses it may move to
TRANSITIONS: dict[str, set[str]] = {
    BOOKED: {CHECKED_IN, COMPLETED, CANCELLED},
    CHECKED_IN: {COMPLETED, CANCELLED},
    COMPLETED: set(),
    CANCELLED: set(),
}


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    specialization: Mapped[str] = mapped_column(String(120))
    room: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_scheduled_at", "scheduled_at"),
        Index("ix_appointments_doctor_scheduled", "doctor_id", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default=BOOKED)
    token_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doctor: Mapped[Doctor] = relationship(back_populates="appointments")
    patient: Mapped[Patient] = relationship(back_populates="appointments")

    @property
    def doctor_name(self) -> str:
        return self.doctor.name

    @property
    def patient_name(self) -> str:
        return self.patient.name
