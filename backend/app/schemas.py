"""Pydantic request/response schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["booked", "checked_in", "completed", "cancelled"]


def _drop_tz(value: datetime | None) -> datetime | None:
    """Clinic times are stored as naive local time; ignore any client timezone."""
    if value is not None and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


# ---------- doctors ----------
class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    specialization: str = Field(min_length=2, max_length=120)
    room: str = Field(default="", max_length=20)


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    specialization: str | None = Field(default=None, min_length=2, max_length=120)
    room: str | None = Field(default=None, max_length=20)


class DoctorOut(DoctorCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- patients ----------
class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=20)
    age: int | None = Field(default=None, ge=0, le=120)


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    age: int | None = Field(default=None, ge=0, le=120)


class PatientOut(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- appointments ----------
class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    scheduled_at: datetime
    reason: str = Field(default="", max_length=255)

    _tz = field_validator("scheduled_at")(_drop_tz)


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)
    status: Status | None = None

    _tz = field_validator("scheduled_at")(_drop_tz)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    doctor_name: str
    patient_name: str
    scheduled_at: datetime
    reason: str
    status: Status
    token_number: int
    created_at: datetime


class QueueEntryOut(AppointmentOut):
    position: int


class StatsOut(BaseModel):
    date: date
    total_today: int
    waiting: int
    booked: int
    checked_in: int
    completed: int
    cancelled: int
    doctors: int
    patients: int
