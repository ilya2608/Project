def test_list_doctors_and_specialties(client, seed_doctor, seed_specialty):
    resp = client.get("/api/v1/doctors")
    assert resp.status_code == 200
    names = [d["full_name"] for d in resp.json()]
    assert "Dr. Test" in names

    specialties_resp = client.get("/api/v1/specialties")
    assert specialties_resp.status_code == 200


def test_get_slots_for_doctor(client, seed_doctor):
    resp = client.get(
        f"/api/v1/doctors/{seed_doctor.id}/slots?date_from=2026-07-07&date_to=2026-07-07"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["date"] == "2026-07-07"
    assert len(body[0]["slots"]) > 0


def test_get_doctor_404_for_unknown_id(client):
    import uuid

    resp = client.get(f"/api/v1/doctors/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_slots_range_too_large_rejected(client, seed_doctor):
    resp = client.get(
        f"/api/v1/doctors/{seed_doctor.id}/slots?date_from=2026-07-07&date_to=2026-12-07"
    )
    assert resp.status_code == 400
