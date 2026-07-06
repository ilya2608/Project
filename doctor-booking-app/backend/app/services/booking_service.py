from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Appointment, AppointmentStatus, DoctorProfile, User


class SlotUnavailableError(Exception):
    pass


def create_appointment(
    db: Session,
    doctor: User,
    patient: User,
    start_at: datetime,
    reason_note: str | None = None,
) -> Appointment:
    profile: DoctorProfile = doctor.doctor_profile
    end_at = start_at + timedelta(minutes=profile.slot_duration_minutes)

    # App-level pre-check: fast, friendly 409 in the common (non-racing) case.
    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.status == AppointmentStatus.booked,
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        )
        .first()
    )
    if conflict is not None:
        raise SlotUnavailableError("This slot was just booked. Please pick another.")

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_at=start_at,
        end_at=end_at,
        status=AppointmentStatus.booked,
        reason_note=reason_note,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError as exc:
        # Authoritative guard: the Postgres EXCLUDE constraint catches races
        # the app-level check above could miss between check and insert.
        db.rollback()
        raise SlotUnavailableError("This slot was just booked. Please pick another.") from exc

    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment: Appointment, by: str) -> Appointment:
    appointment.status = (
        AppointmentStatus.cancelled_by_patient if by == "patient" else AppointmentStatus.cancelled_by_doctor
    )
    appointment.cancelled_at = datetime.now(timezone.utc)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def reschedule_appointment(db: Session, appointment: Appointment, new_start_at: datetime) -> Appointment:
    doctor = db.get(User, appointment.doctor_id)
    patient = db.get(User, appointment.patient_id)
    cancel_appointment(db, appointment, by="doctor")
    return create_appointment(db, doctor, patient, new_start_at, appointment.reason_note)
