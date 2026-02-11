from fastapi.testclient import TestClient
import pytest
import uuid

@pytest.fixture
def analytics_security_setup(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    email_t = f"t_an_sec_{uid}@test.com"
    email_s1 = f"s1_an_sec_{uid}@test.com"
    email_s2 = f"s2_an_sec_{uid}@test.com"

    # Register Teacher
    client.post("/auth/register", json={"email": email_t, "password": "pw", "first_name": "T", "last_name": "E", "is_teacher": True})
    token_t = client.post("/auth/token", data={"username": email_t, "password": "pw"}).json()["access_token"]

    # Register Student 1
    client.post("/auth/register", json={"email": email_s1, "password": "pw", "first_name": "S", "last_name": "1", "is_teacher": False})
    token_s1 = client.post("/auth/token", data={"username": email_s1, "password": "pw"}).json()["access_token"]

    # Register Student 2
    s2_resp = client.post("/auth/register", json={"email": email_s2, "password": "pw", "first_name": "S", "last_name": "2", "is_teacher": False})
    user_s2_id = s2_resp.json()["id"]

    # Get Student 2's Profile ID
    students = client.get("/school/students").json()
    s2_profile_id = next(s["id"] for s in students if s["user_id"] == user_s2_id)

    return {
        "headers_t": {"Authorization": f"Bearer {token_t}"},
        "headers_s1": {"Authorization": f"Bearer {token_s1}"},
        "s2_profile_id": s2_profile_id
    }

def test_student_view_other_student_analytics_forbidden(client: TestClient, analytics_security_setup):
    s = analytics_security_setup
    # Student 1 tries to view Student 2's analytics
    resp = client.get(
        f"/analytics/students/{s['s2_profile_id']}",
        headers=s["headers_s1"]
    )
    assert resp.status_code == 403

def test_anon_view_analytics_unauthorized(client: TestClient, analytics_security_setup):
    s = analytics_security_setup
    resp = client.get(f"/analytics/students/{s['s2_profile_id']}")
    assert resp.status_code == 401

def test_teacher_view_student_analytics_allowed(client: TestClient, analytics_security_setup):
    s = analytics_security_setup
    # Teacher tries to view Student 2's analytics - Should be allowed
    resp = client.get(
        f"/analytics/students/{s['s2_profile_id']}",
        headers=s["headers_t"]
    )
    assert resp.status_code == 200
    # Response might be empty structure if no data, but status 200 confirms access.
