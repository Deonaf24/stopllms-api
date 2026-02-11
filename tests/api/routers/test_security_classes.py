from fastapi.testclient import TestClient
from datetime import date
import pytest
import uuid

@pytest.fixture
def security_setup(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    email_ta = f"t_class_a_{uid}@sec.com"
    email_tb = f"t_class_b_{uid}@sec.com"
    email_st = f"s_class_{uid}@sec.com"

    # Register users
    client.post("/auth/register", json={"email": email_ta, "password": "pw", "first_name": "T", "last_name": "A", "is_teacher": True})
    token_ta = client.post("/auth/token", data={"username": email_ta, "password": "pw"}).json()["access_token"]
    
    client.post("/auth/register", json={"email": email_tb, "password": "pw", "first_name": "T", "last_name": "B", "is_teacher": True})
    token_tb = client.post("/auth/token", data={"username": email_tb, "password": "pw"}).json()["access_token"]

    client.post("/auth/register", json={"email": email_st, "password": "pw", "first_name": "S", "last_name": "T", "is_teacher": False})
    token_st = client.post("/auth/token", data={"username": email_st, "password": "pw"}).json()["access_token"]

    # Get Teacher A Profile ID
    t_headers = {"Authorization": f"Bearer {token_ta}"}
    ta_user_id = client.get("/auth/users/me/", headers=t_headers).json()["id"]
    teachers = client.get("/school/teachers").json()
    ta_profile_id = next(t["id"] for t in teachers if t["user_id"] == ta_user_id)
    
    # Get Teacher B Profile ID
    tb_headers = {"Authorization": f"Bearer {token_tb}"}
    tb_user_id = client.get("/auth/users/me/", headers=tb_headers).json()["id"]
    tb_profile_id = next(t["id"] for t in teachers if t["user_id"] == tb_user_id)

    return {
        "token_ta": token_ta,
        "token_tb": token_tb,
        "token_st": token_st,
        "ta_profile_id": ta_profile_id,
        "tb_profile_id": tb_profile_id
    }

def test_anon_create_class_unauthorized(client: TestClient, security_setup):
    s = security_setup
    resp = client.post(
        "/school/classes",
        json={"name": "Anon", "teacher_id": s["ta_profile_id"], "start_date": str(date.today()), "end_date": str(date.today()), "period": "1"}
    )
    assert resp.status_code == 401

def test_student_create_class_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.post(
        "/school/classes",
        json={"name": "Student Hack", "teacher_id": s["ta_profile_id"], "start_date": str(date.today()), "end_date": str(date.today()), "period": "1"},
        headers={"Authorization": f"Bearer {s['token_st']}"}
    )
    assert resp.status_code == 403

def test_teacher_create_class_for_other_forbidden(client: TestClient, security_setup):
    s = security_setup
    # Teacher B tries to create class for Teacher A
    resp = client.post(
        "/school/classes",
        json={"name": "Impersonation", "teacher_id": s["ta_profile_id"], "start_date": str(date.today()), "end_date": str(date.today()), "period": "1"},
        headers={"Authorization": f"Bearer {s['token_tb']}"}
    )
    assert resp.status_code == 403
