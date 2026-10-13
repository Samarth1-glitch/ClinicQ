from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.metrics import APPOINTMENTS_BOOKED, APPOINTMENTS_CANCELLED
from app.models import (
    BOOKED,
    CANCELLED,
    CHECKED_IN,
    COMPLETED,
    TRANSITIONS,
    Appointment,
    Doctor,
    Patient,
)
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentUpdate,
    QueueEntryOut,
    StatsOut,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])
queue_router = APIRouter(prefix="/queue", tags=["queue"])


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)


def _with_names():
    return (
        select(Appointment)
        .options(joinedload(Appointment.doctor), joinedload(Appointment.patient))
    )


def _get_or_404(db: Session, appointment_id: int) -> Appointment:
    appt = db.scalars(_with_names().where(Appointment.id == appointment_id)).first()
    if appt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    return appt


def _assert_slot_free(
    db: Session, doctor_id: int, when: datetime, exclude_id: int | None = None
) -> None:
    stmt = select(func.count()).select_from(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_at == when,
        Appointment.status != CANCELLED,
    )
    if exclude_id is not None:
        stmt = stmt.where(Appointment.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(status.HTTP_409_CONFLICT, "That time slot is already booked")


# NOTE: /stats must be declared before /{appointment_id}
@router.get("/stats", response_model=StatsOut)
def appointment_stats(db: Session = Depends(get_db)):
    today = date.today()
    start, end = _day_bounds(today)
    rows = db.execute(
        select(Appointment.status, func.count())
        .where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
        .group_by(Appointment.status)
    ).all()
    counts = {s: c for s, c in rows}
    booked = counts.get(BOOKED, 0)
    checked_in = counts.get(CHECKED_IN, 0)
    return StatsOut(
        date=today,
        total_today=sum(counts.values()),
        waiting=booked + checked_in,
        booked=booked,
        checked_in=checked_in,
        completed=counts.get(COMPLETED, 0),
        cancelled=counts.get(CANCELLED, 0),
        doctors=db.scalar(select(func.count()).select_from(Doctor)) or 0,
        patients=db.scalar(select(func.count()).select_from(Patient)) or 0,
    )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    day: date | None = Query(default=None, alias="date"),
    doctor_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = _with_names().order_by(Appointment.scheduled_at, Appointment.token_number)
    if day:
        start, end = _day_bounds(day)
        stmt = stmt.where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter)
    return db.scalars(stmt.limit(limit)).all()


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    if db.get(Doctor, payload.doctor_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    if db.get(Patient, payload.patient_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    _assert_slot_free(db, payload.doctor_id, payload.scheduled_at)

    start, end = _day_bounds(payload.scheduled_at.date())
    last_token = db.scalar(
        select(func.max(Appointment.token_number)).where(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
        )
    )
    appt = Appointment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        scheduled_at=payload.scheduled_at,
        reason=payload.reason,
        status=BOOKED,
        token_number=(last_token or 0) + 1,
    )
    db.add(appt)
    db.commit()
    APPOINTMENTS_BOOKED.inc()
    return _get_or_404(db, appt.id)


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, appointment_id)


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)
):
    appt = _get_or_404(db, appointment_id)
    data = payload.model_dump(exclude_unset=True)

    new_status = data.get("status")
    if new_status is not None and new_status != appt.status:
        if new_status not in TRANSITIONS[appt.status]:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Cannot change status from '{appt.status}' to '{new_status}'",
            )
        appt.status = new_status
        if new_status == CANCELLED:
            APPOINTMENTS_CANCELLED.inc()

    new_time = data.get("scheduled_at")
    if new_time is not None and new_time != appt.scheduled_at:
        if appt.status in (COMPLETED, CANCELLED):
            raise HTTPException(status.HTTP_409_CONFLICT, "Closed appointments cannot be moved")
        _assert_slot_free(db, appt.doctor_id, new_time, exclude_id=appt.id)
        appt.scheduled_at = new_time

    if data.get("reason") is not None:
        appt.reason = data["reason"]

    db.commit()
    return _get_or_404(db, appointment_id)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = _get_or_404(db, appointment_id)
    db.delete(appt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@queue_router.get("", response_model=list[QueueEntryOut])
def live_queue(doctor_id: int | None = None, db: Session = Depends(get_db)):
    """Today's waiting patients (booked + checked in), numbered per doctor."""
    start, end = _day_bounds(date.today())
    stmt = (
        _with_names()
        .where(
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
            Appointment.status.in_([BOOKED, CHECKED_IN]),
        )
        .order_by(Appointment.doctor_id, Appointment.scheduled_at, Appointment.token_number)
    )
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)

    entries: list[QueueEntryOut] = []
    position: dict[int, int] = {}
    for appt in db.scalars(stmt).all():
        position[appt.doctor_id] = position.get(appt.doctor_id, 0) + 1
        base = AppointmentOut.model_validate(appt).model_dump()
        entries.append(QueueEntryOut(**base, position=position[appt.doctor_id]))
    return entries
