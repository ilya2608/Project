from tests.conftest import login_as


def test_patient_can_book_and_cancel_own_appointment(client, db_session, seed_doctor, seed_patient):
    login_as(client, db_session, seed_patient)

    resp = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(seed_doctor.id), "start_at": "2026-07-07T09:00:00+02:00"},
    )
    assert resp.status_code == 201
    appointment_id = resp.json()["id"]

    cancel_resp = client.post(f"/api/v1/appointments/{appointment_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled_by_patient"


def test_booking_conflict_returns_409(client, db_session, seed_doctor, seed_patient):
    login_as(client, db_session, seed_patient)
    payload = {"doctor_id": str(seed_doctor.id), "start_at": "2026-07-07T09:00:00+02:00"}

    first = client.post("/api/v1/appointments", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/appointments", json=payload)
    assert second.status_code == 409


def test_patient_cannot_cancel_another_patients_appointment(client, db_session, seed_doctor, seed_patient):
    from app.db.models import AuthProvider, PatientProfile, User, UserRole

    other_patient = User(role=UserRole.patient, full_name="Other Patient", auth_provider=AuthProvider.itsme)
    db_session.add(other_patient)
    db_session.flush()
    db_session.add(PatientProfile(user_id=other_patient.id, itsme_sub="mock-other-patient"))
    db_session.commit()

    login_as(client, db_session, seed_patient)
    book_resp = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(seed_doctor.id), "start_at": "2026-07-07T09:00:00+02:00"},
    )
    appointment_id = book_resp.json()["id"]

    client.cookies.clear()
    login_as(client, db_session, other_patient)
    cancel_resp = client.post(f"/api/v1/appointments/{appointment_id}/cancel")
    assert cancel_resp.status_code == 403


def test_doctor_sees_booked_appointment_in_their_agenda(client, db_session, seed_doctor, seed_patient):
    login_as(client, db_session, seed_patient)
    client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(seed_doctor.id), "start_at": "2026-07-07T09:00:00+02:00"},
    )

    client.cookies.clear()
    login_as(client, db_session, seed_doctor)
    agenda_resp = client.get("/api/v1/appointments/doctor/mine")
    assert agenda_resp.status_code == 200
    assert len(agenda_resp.json()) == 1


def test_unauthenticated_request_rejected(client):
    resp = client.get("/api/v1/appointments/mine")
    assert resp.status_code == 401
