from tests.conftest import login_as


def test_doctor_can_manage_own_availability(client, db_session, seed_doctor):
    login_as(client, db_session, seed_doctor)

    create_resp = client.post(
        f"/api/v1/doctors/{seed_doctor.id}/availability/rules",
        json={"weekday": 5, "start_time": "10:00:00", "end_time": "12:00:00"},
    )
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]

    list_resp = client.get(f"/api/v1/doctors/{seed_doctor.id}/availability/rules")
    assert any(r["id"] == rule_id for r in list_resp.json())

    delete_resp = client.delete(f"/api/v1/doctors/{seed_doctor.id}/availability/rules/{rule_id}")
    assert delete_resp.status_code == 204


def test_doctor_cannot_edit_another_doctors_availability(client, db_session, seed_doctor):
    from app.core.security import hash_password
    from app.db.models import AuthProvider, DoctorProfile, User, UserRole

    other_doctor = User(role=UserRole.doctor, email="other-doc@example.com", full_name="Dr. Other", auth_provider=AuthProvider.internal)
    db_session.add(other_doctor)
    db_session.flush()
    db_session.add(DoctorProfile(user_id=other_doctor.id, password_hash=hash_password("pw"), slot_duration_minutes=30))
    db_session.commit()

    login_as(client, db_session, seed_doctor)
    resp = client.post(
        f"/api/v1/doctors/{other_doctor.id}/availability/rules",
        json={"weekday": 5, "start_time": "10:00:00", "end_time": "12:00:00"},
    )
    assert resp.status_code == 403


def test_admin_can_edit_any_doctors_availability(client, db_session, seed_doctor, seed_admin):
    login_as(client, db_session, seed_admin)
    resp = client.post(
        f"/api/v1/doctors/{seed_doctor.id}/availability/exceptions",
        json={"date": "2026-08-01", "kind": "block", "is_full_day_block": True},
    )
    assert resp.status_code == 201


def test_patient_cannot_touch_availability(client, db_session, seed_doctor, seed_patient):
    login_as(client, db_session, seed_patient)
    resp = client.get(f"/api/v1/doctors/{seed_doctor.id}/availability/rules")
    assert resp.status_code == 403
