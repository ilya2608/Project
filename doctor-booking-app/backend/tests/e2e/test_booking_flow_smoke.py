from tests.conftest import login_as


def test_golden_path_booking_flow(client, db_session, seed_doctor, seed_patient):
    """Seed -> patient books -> shows in 'my appointments' -> doctor sees it in
    their agenda -> patient cancels -> slot is free again. Proves the whole
    stack (auth, availability, slot engine, booking, cancellation) works
    together, not just each piece in isolation."""

    login_as(client, db_session, seed_patient)

    doctors_resp = client.get("/api/v1/doctors")
    assert doctors_resp.status_code == 200
    doctor_ids = [d["id"] for d in doctors_resp.json()]
    assert str(seed_doctor.id) in doctor_ids

    slots_resp = client.get(
        f"/api/v1/doctors/{seed_doctor.id}/slots?date_from=2026-07-07&date_to=2026-07-07"
    )
    first_slot = slots_resp.json()[0]["slots"][0]

    book_resp = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(seed_doctor.id), "start_at": first_slot["start_at"]},
    )
    assert book_resp.status_code == 201
    appointment_id = book_resp.json()["id"]

    mine_resp = client.get("/api/v1/appointments/mine")
    assert any(a["id"] == appointment_id for a in mine_resp.json())

    client.cookies.clear()
    login_as(client, db_session, seed_doctor)
    doctor_agenda_resp = client.get("/api/v1/appointments/doctor/mine")
    assert any(a["id"] == appointment_id for a in doctor_agenda_resp.json())

    client.cookies.clear()
    login_as(client, db_session, seed_patient)
    cancel_resp = client.post(f"/api/v1/appointments/{appointment_id}/cancel")
    assert cancel_resp.status_code == 200

    slots_after_cancel = client.get(
        f"/api/v1/doctors/{seed_doctor.id}/slots?date_from=2026-07-07&date_to=2026-07-07"
    ).json()[0]["slots"]
    assert first_slot["start_at"] in [s["start_at"] for s in slots_after_cancel]
