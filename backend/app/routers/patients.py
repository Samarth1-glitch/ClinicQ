from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, Patient
from app.schemas import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


def _get_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(
    q: str | None = Query(default=None, description="Search by name"),
    db: Session = Depends(get_db),
):
    stmt = select(Patient).order_by(Patient.name)
    if q:
        stmt = stmt.where(Patient.name.ilike(f"%{q}%"))
    return db.scalars(stmt).all()


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, patient_id)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    in_use = db.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.patient_id == patient_id)
    )
    if in_use:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Patient has appointments and cannot be deleted"
        )
    db.delete(patient)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
