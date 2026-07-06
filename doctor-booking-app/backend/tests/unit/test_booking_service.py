import threading
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.models import (
    AuthProvider,
    DoctorProfile,
    PatientProfile,
    User,
    UserRole,
    WeeklyAvailabilityRule,
)
from app.services.booking_service import SlotUnavailableError, cancel_appointment, create_appointment

TZ = ZoneInfo("Europe/Brussels")


def test_booking_a_free_slot_succeeds(db_session, seed_doctor, seed_patient):
    start = datetime(2026, 7, 7, 9, 0, tzinfo=TZ)
    appt = create_appointment(db_session, seed_doctor, seed_patient, start)
    assert appt.start_at == start
    assert appt.end_at == datetime(2026, 7, 7, 9, 30, tzinfo=TZ)


def test_booking_an_already_booked_slot_raises(db_session, seed_doctor, seed_patient):
    start = datetime(2026, 7, 7, 9, 0, tzinfo=TZ)
    create_appointment(db_session, seed_doctor, seed_patient, start)
    with pytest.raises(SlotUnavailableError):
        create_appointment(db_session, seed_doctor, seed_patient, start)


def test_cancelling_frees_the_slot_for_rebooking(db_session, seed_doctor, seed_patient):
    start = datetime(2026, 7, 7, 9, 0, tzinfo=TZ)
    appt = create_appointment(db_session, seed_doctor, seed_patient, start)
    cancel_appointment(db_session, appt, by="patient")

    rebooked = create_appointment(db_session, seed_doctor, seed_patient, start)
    assert rebooked.id != appt.id


def test_concurrent_bookings_for_same_slot_only_one_succeeds(engine):
    """Exercises the Postgres EXCLUDE constraint directly: two independent DB
    sessions racing to book the exact same doctor/slot must not both win."""
    SessionLocal = sessionmaker(bind=engine)

    setup_session = SessionLocal()
    doctor_user = User(role=UserRole.doctor, email="race-doc@example.com", full_name="Dr. Race", auth_provider=AuthProvider.internal)
    setup_session.add(doctor_user)
    setup_session.flush()
    setup_session.add(DoctorProfile(user_id=doctor_user.id, password_hash=hash_password("pw"), slot_duration_minutes=30))
    setup_session.add(WeeklyAvailabilityRule(doctor_id=doctor_user.id, weekday=1, start_time=time(9, 0), end_time=time(12, 0)))

    patient_user = User(role=UserRole.patient, full_name="Race Patient", auth_provider=AuthProvider.itsme)
    setup_session.add(patient_user)
    setup_session.flush()
    setup_session.add(PatientProfile(user_id=patient_user.id, itsme_sub="mock-race-patient"))
    setup_session.commit()

    doctor_id, patient_id = doctor_user.id, patient_user.id
    setup_session.close()

    start = datetime(2026, 7, 7, 9, 0, tzinfo=TZ)
    results: list[str] = []

    def attempt_booking():
        session = SessionLocal()
        try:
            doctor = session.get(User, doctor_id)
            patient = session.get(User, patient_id)
            create_appointment(session, doctor, patient, start)
            results.append("success")
        except SlotUnavailableError:
            results.append("conflict")
        finally:
            session.close()

    threads = [threading.Thread(target=attempt_booking) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("success") == 1
    assert results.count("conflict") == 4
