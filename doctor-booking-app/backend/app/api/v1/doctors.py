import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import DoctorProfile, Specialty, User, UserRole
from app.schemas.availability import SlotOut, SlotsByDate
from app.schemas.doctor import DoctorOut, SpecialtyOut
from app.services.slot_engine import compute_slots

router = APIRouter(tags=["doctors"])

MAX_SLOT_QUERY_DAYS = 60


@router.get("/specialties", response_model=list[SpecialtyOut])
def list_specialties(db: Session = Depends(get_db)) -> list[Specialty]:
    return db.query(Specialty).order_by(Specialty.name).all()


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(
    specialty_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DoctorOut]:
    query = (
        db.query(User)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .options(joinedload(User.doctor_profile).joinedload(DoctorProfile.specialty))
        .filter(User.role == UserRole.doctor, User.is_active.is_(True))
    )
    if specialty_id is not None:
        query = query.filter(DoctorProfile.specialty_id == specialty_id)

    return [_to_doctor_out(u) for u in query.all()]


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: uuid.UUID, db: Session = Depends(get_db)) -> DoctorOut:
    user = _get_doctor_or_404(db, doctor_id)
    return _to_doctor_out(user)


@router.get("/doctors/{doctor_id}/slots", response_model=list[SlotsByDate])
def get_doctor_slots(
    doctor_id: uuid.UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[SlotsByDate]:
    if date_to < date_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to must be >= date_from")
    if (date_to - date_from).days > MAX_SLOT_QUERY_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Range too large; max {MAX_SLOT_QUERY_DAYS} days",
        )

    user = _get_doctor_or_404(db, doctor_id)
    profile = user.doctor_profile
    if not profile.is_accepting_bookings:
        return [
            SlotsByDate(date=date_from + timedelta(days=i), slots=[])
            for i in range((date_to - date_from).days + 1)
        ]

    day_slots = compute_slots(
        db,
        doctor_id=doctor_id,
        slot_duration_minutes=profile.slot_duration_minutes,
        date_from=date_from,
        date_to=date_to,
        clinic_timezone=settings.clinic_timezone,
    )
    return [
        SlotsByDate(date=ds.date, slots=[SlotOut(start_at=s, end_at=e) for s, e in ds.slots]) for ds in day_slots
    ]


def _get_doctor_or_404(db: Session, doctor_id: uuid.UUID) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.doctor_profile).joinedload(DoctorProfile.specialty))
        .filter(User.id == doctor_id, User.role == UserRole.doctor)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return user


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
