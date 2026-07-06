import os
import uuid
from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://agenda:agenda@localhost:5432/agenda_test"
)

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base, get_db  # noqa: E402
from app.db.models import (  # noqa: E402
    AdminProfile,
    AuthProvider,
    DoctorProfile,
    Specialty,
    User,
    UserRole,
    WeeklyAvailabilityRule,
)
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    from sqlalchemy import text

    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        conn.commit()
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    with eng.connect() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE appointments
                ADD CONSTRAINT no_overlapping_doctor_appointments
                EXCLUDE USING gist (
                    doctor_id WITH =,
                    tstzrange(start_at, end_at) WITH &&
                )
                WHERE (status = 'booked')
                """
            )
        )
        conn.commit()
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_doctor(db_session):
    """A doctor with Mon-Fri 09:00-12:00 / 13:00-17:00 availability, 30 min slots."""
    user = User(role=UserRole.doctor, email="doc@example.com", full_name="Dr. Test", auth_provider=AuthProvider.internal)
    db_session.add(user)
    db_session.flush()
    profile = DoctorProfile(user_id=user.id, password_hash=hash_password("pw"), slot_duration_minutes=30)
    db_session.add(profile)
    for weekday in range(5):
        db_session.add(WeeklyAvailabilityRule(doctor_id=user.id, weekday=weekday, start_time=time(9, 0), end_time=time(12, 0)))
        db_session.add(WeeklyAvailabilityRule(doctor_id=user.id, weekday=weekday, start_time=time(13, 0), end_time=time(17, 0)))
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def seed_patient(db_session):
    from app.db.models import PatientProfile

    user = User(role=UserRole.patient, full_name="Test Patient", auth_provider=AuthProvider.itsme)
    db_session.add(user)
    db_session.flush()
    db_session.add(PatientProfile(user_id=user.id, itsme_sub=f"mock-{uuid.uuid4()}"))
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def seed_admin(db_session):
    user = User(role=UserRole.admin, email="admin@example.com", full_name="Admin", auth_provider=AuthProvider.internal)
    db_session.add(user)
    db_session.flush()
    db_session.add(AdminProfile(user_id=user.id, password_hash=hash_password("pw")))
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def seed_specialty(db_session):
    specialty = Specialty(name="General Practice", slug="general-practice")
    db_session.add(specialty)
    db_session.commit()
    db_session.refresh(specialty)
    return specialty


def login_as(client: TestClient, db_session, user: User) -> None:
    """Directly creates a session and cookie for `user`, bypassing the login UI."""
    from fastapi import Response

    from app.auth.session_store import create_session

    response = Response()
    create_session(db_session, user, response)
    cookie_header = response.headers.get("set-cookie")
    # Extract "session_id=<value>" from the Set-Cookie header and apply it to the client.
    session_id = cookie_header.split("session_id=")[1].split(";")[0]
    client.cookies.set("session_id", session_id)
