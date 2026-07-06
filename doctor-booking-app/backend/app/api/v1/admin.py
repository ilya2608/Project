import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_role
from app.core.security import hash_password
from app.db.base import get_db
from app.db.models import (
    Appointment,
    AppointmentStatus,
    AuthProvider,
    DoctorProfile,
    Specialty,
    User,
    UserRole,
)
from app.schemas.admin import AdminAppointmentOut
from app.schemas.doctor import DoctorCreate, DoctorOut, DoctorUpdate, SpecialtyCreate, SpecialtyOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role(UserRole.admin))])


@router.get("/doctors", response_model=list[DoctorOut])
def list_all_doctors(db: Session = Depends(get_db)) -> list[DoctorOut]:
    users = (
        db.query(User)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .options(joinedload(User.doctor_profile).joinedload(DoctorProfile.specialty))
        .filter(User.role == UserRole.doctor)
        .all()
    )
    return [_to_doctor_out(u) for u in users]


@router.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)) -> DoctorOut:
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = User(
        role=UserRole.doctor,
        email=payload.email,
        full_name=payload.full_name,
        auth_provider=AuthProvider.internal,
    )
    db.add(user)
    db.flush()

    profile = DoctorProfile(
        user_id=user.id,
        specialty_id=payload.specialty_id,
        bio=payload.bio,
        password_hash=hash_password(payload.password),
        slot_duration_minutes=payload.slot_duration_minutes,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return _to_doctor_out(user)


@router.put("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: uuid.UUID, payload: DoctorUpdate, db: Session = Depends(get_db)) -> DoctorOut:
    user = db.query(User).filter(User.id == doctor_id, User.role == UserRole.doctor).first()
    if user is None or user.doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    profile = user.doctor_profile
    updates = payload.model_dump(exclude_unset=True)
    if "full_name" in updates:
        user.full_name = updates.pop("full_name")
    for field, value in updates.items():
        setattr(profile, field, value)

    db.add(user)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return _to_doctor_out(user)


@router.post("/specialties", response_model=SpecialtyOut, status_code=status.HTTP_201_CREATED)
def create_specialty(payload: SpecialtyCreate, db: Session = Depends(get_db)) -> Specialty:
    if db.query(Specialty).filter(Specialty.slug == payload.slug).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specialty slug already in use")

    specialty = Specialty(**payload.model_dump())
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    return specialty


@router.get("/appointments", response_model=list[AdminAppointmentOut])
def list_all_appointments(
    doctor_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    appointment_status: AppointmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[AdminAppointmentOut]:
    query = db.query(Appointment)
    if doctor_id is not None:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if date_from is not None:
        query = query.filter(Appointment.start_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to is not None:
        query = query.filter(Appointment.start_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))
    if appointment_status is not None:
        query = query.filter(Appointment.status == appointment_status)

    appointments = query.order_by(Appointment.start_at).all()
    user_ids = {a.doctor_id for a in appointments} | {a.patient_id for a in appointments}
    users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return [
        AdminAppointmentOut(
            id=a.id,
            doctor_id=a.doctor_id,
            doctor_name=users_by_id[a.doctor_id].full_name if a.doctor_id in users_by_id else "Unknown",
            patient_id=a.patient_id,
            patient_name=users_by_id[a.patient_id].full_name if a.patient_id in users_by_id else "Unknown",
            start_at=a.start_at,
            end_at=a.end_at,
            status=a.status,
        )
        for a in appointments
    ]


def _to_doctor_out(user: User) -> DoctorOut:
    profile = user.doctor_profile
    return DoctorOut(
        id=user.id,
        full_name=user.full_name,
        bio=profile.bio,
        specialty=profile.specialty,
        slot_duration_minutes=profile.slot_duration_minutes,
        is_accepting_bookings=profile.is_accepting_bookings,
    )
