"""Seeds specialties, a couple of doctors with weekly availability, and an
admin account, for local development/demo purposes.

Usage: python -m scripts.seed_dev_data
"""

from datetime import time

from app.core.security import hash_password
from app.db.base import SessionLocal
from app.db.models import (
    AdminProfile,
    AuthProvider,
    DoctorProfile,
    Specialty,
    User,
    UserRole,
    WeeklyAvailabilityRule,
)

DOCTOR_PASSWORD = "doctor-demo-pass"
ADMIN_PASSWORD = "admin-demo-pass"


def run() -> None:
    db = SessionLocal()
    try:
        general = db.query(Specialty).filter(Specialty.slug == "general-practice").first()
        if general is None:
            general = Specialty(name="General Practice", slug="general-practice")
            db.add(general)

        dermatology = db.query(Specialty).filter(Specialty.slug == "dermatology").first()
        if dermatology is None:
            dermatology = Specialty(name="Dermatology", slug="dermatology")
            db.add(dermatology)

        db.flush()

        if db.query(User).filter(User.email == "dr.peeters@example.com").first() is None:
            doctor_user = User(
                role=UserRole.doctor,
                email="dr.peeters@example.com",
                full_name="Dr. An Peeters",
                auth_provider=AuthProvider.internal,
            )
            db.add(doctor_user)
            db.flush()
            db.add(
                DoctorProfile(
                    user_id=doctor_user.id,
                    specialty_id=general.id,
                    bio="General practitioner, 15 years of experience.",
                    password_hash=hash_password(DOCTOR_PASSWORD),
                    slot_duration_minutes=30,
                )
            )
            for weekday in range(5):  # Monday..Friday
                db.add(
                    WeeklyAvailabilityRule(
                        doctor_id=doctor_user.id, weekday=weekday, start_time=time(9, 0), end_time=time(12, 30)
                    )
                )
                db.add(
                    WeeklyAvailabilityRule(
                        doctor_id=doctor_user.id, weekday=weekday, start_time=time(14, 0), end_time=time(17, 0)
                    )
                )

        if db.query(User).filter(User.email == "dr.willems@example.com").first() is None:
            doctor_user2 = User(
                role=UserRole.doctor,
                email="dr.willems@example.com",
                full_name="Dr. Tom Willems",
                auth_provider=AuthProvider.internal,
            )
            db.add(doctor_user2)
            db.flush()
            db.add(
                DoctorProfile(
                    user_id=doctor_user2.id,
                    specialty_id=dermatology.id,
                    bio="Dermatologist specializing in skin conditions.",
                    password_hash=hash_password(DOCTOR_PASSWORD),
                    slot_duration_minutes=20,
                )
            )
            for weekday in (1, 3):  # Tue, Thu
                db.add(
                    WeeklyAvailabilityRule(
                        doctor_id=doctor_user2.id, weekday=weekday, start_time=time(10, 0), end_time=time(16, 0)
                    )
                )

        if db.query(User).filter(User.email == "admin@example.com").first() is None:
            admin_user = User(
                role=UserRole.admin,
                email="admin@example.com",
                full_name="Clinic Admin",
                auth_provider=AuthProvider.internal,
            )
            db.add(admin_user)
            db.flush()
            db.add(AdminProfile(user_id=admin_user.id, password_hash=hash_password(ADMIN_PASSWORD)))

        db.commit()
        print("Seed complete.")
        print(f"  Doctor login: dr.peeters@example.com / {DOCTOR_PASSWORD}")
        print(f"  Doctor login: dr.willems@example.com / {DOCTOR_PASSWORD}")
        print(f"  Admin login: admin@example.com / {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
