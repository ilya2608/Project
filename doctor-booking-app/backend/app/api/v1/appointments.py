import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.base import get_db
from app.db.models import Appointment, AppointmentStatus, User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentReschedule
from app.services.booking_service import (
    SlotUnavailableError,
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    patient: User = Depends(require_role(UserRole.patient)),
) -> Appointment:
    doctor = db.get(User, payload.doctor_id)
    if doctor is None or doctor.role != UserRole.doctor or doctor.doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if not doctor.doctor_profile.is_accepting_bookings:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This doctor is not accepting bookings")

    try:
        return create_appointment(db, doctor, patient, payload.start_at, payload.reason_note)
    except SlotUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/mine", response_model=list[AppointmentOut])
def my_appointments(
    db: Session = Depends(get_db),
    patient: User = Depends(require_role(UserRole.patient)),
) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .order_by(Appointment.start_at.desc())
        .all()
    )


@router.get("/doctor/mine", response_model=list[AppointmentOut])
def doctor_agenda(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    doctor: User = Depends(require_role(UserRole.doctor)),
) -> list[Appointment]:
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor.id)
    if date_from is not None:
        query = query.filter(Appointment.start_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to is not None:
        query = query.filter(Appointment.start_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))
    return query.order_by(Appointment.start_at).all()


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(
    appointment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)

    if user.role == UserRole.patient:
        if appointment.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
        by = "patient"
    elif user.role == UserRole.doctor:
        if appointment.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
        by = "doctor"
    elif user.role == UserRole.admin:
        by = "doctor"
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if appointment.status != AppointmentStatus.booked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment is not active")

    return cancel_appointment(db, appointment, by=by)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule(
    appointment_id: uuid.UUID,
    payload: AppointmentReschedule,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)

    if user.role == UserRole.doctor and appointment.doctor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    if user.role not in (UserRole.doctor, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if appointment.status != AppointmentStatus.booked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment is not active")

    try:
        return reschedule_appointment(db, appointment, payload.new_start_at)
    except SlotUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def _get_appointment_or_404(db: Session, appointment_id: uuid.UUID) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment
