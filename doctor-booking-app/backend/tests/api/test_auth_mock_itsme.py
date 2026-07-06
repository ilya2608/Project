import re


def _login_via_mock_itsme(client, given_name="Jean", family_name="Dupont", national_number="85073003328"):
    login_resp = client.get("/api/v1/auth/itsme/login", follow_redirects=False)
    assert login_resp.status_code in (302, 307)
    consent_url = login_resp.headers["location"]
    state = re.search(r"state=([^&]+)", consent_url).group(1)

    consent_resp = client.get(consent_url)
    assert consent_resp.status_code == 200
    assert "MOCK itsme" in consent_resp.text

    submit_resp = client.post(
        "/api/v1/auth/mock-itsme/consent",
        data={
            "state": state,
            "given_name": given_name,
            "family_name": family_name,
            "fake_national_number": national_number,
        },
        follow_redirects=False,
    )
    assert submit_resp.status_code == 303
    callback_url = submit_resp.headers["location"]

    callback_resp = client.get(callback_url, follow_redirects=False)
    assert callback_resp.status_code == 307
    return callback_resp


def test_full_mock_itsme_login_sets_session_and_identity(client):
    _login_via_mock_itsme(client)

    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["role"] == "patient"
    assert body["full_name"] == "Jean Dupont"


def test_repeat_login_as_same_fake_identity_reuses_patient_profile(client):
    _login_via_mock_itsme(client, given_name="Marie", family_name="Claes", national_number="90010112345")
    first_me = client.get("/api/v1/auth/me").json()

    client.post("/api/v1/auth/logout")
    _login_via_mock_itsme(client, given_name="Marie", family_name="Claes", national_number="90010112345")
    second_me = client.get("/api/v1/auth/me").json()

    assert first_me["id"] == second_me["id"]


def test_staff_login_wrong_password_rejected(client, seed_admin):
    resp = client.post(
        "/api/v1/auth/staff/login", json={"email": "admin@example.com", "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_staff_login_correct_password_sets_session(client, seed_admin):
    resp = client.post("/api/v1/auth/staff/login", json={"email": "admin@example.com", "password": "pw"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"

    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.json()["role"] == "admin"


def test_logout_invalidates_session(client):
    _login_via_mock_itsme(client)
    assert client.get("/api/v1/auth/me").status_code == 200

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401
