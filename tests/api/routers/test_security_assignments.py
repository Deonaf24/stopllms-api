from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest
import uuid

@pytest.fixture
def security_setup(client: TestClient):
    # Setup Teachers and Student
    # Unique emails to avoid collisions
    uid = str(uuid.uuid4())[:8]
    email_ta = f"teacha_{uid}@sec.com"
    email_tb = f"teachb_{uid}@sec.com"
    email_st = f"stud_{uid}@sec.com"

    # Teacher A
    client.post("/auth/register", json={"email": email_ta, "password": "pw", "first_name": "T", "last_name": "A", "is_teacher": True})
    token_ta = client.post("/auth/token", data={"username": email_ta, "password": "pw"}).json()["access_token"]
    
    # Teacher B
    client.post("/auth/register", json={"email": email_tb, "password": "pw", "first_name": "T", "last_name": "B", "is_teacher": True})
    token_tb = client.post("/auth/token", data={"username": email_tb, "password": "pw"}).json()["access_token"]
    
    # Student
    client.post("/auth/register", json={"email": email_st, "password": "pw", "first_name": "S", "last_name": "T", "is_teacher": False})
    token_st = client.post("/auth/token", data={"username": email_st, "password": "pw"}).json()["access_token"]
    
    # Teacher A Setup
    t_headers = {"Authorization": f"Bearer {token_ta}"}
    ta_id = client.get("/auth/users/me/", headers=t_headers).json()["id"]
    teachers = client.get("/school/teachers").json()
    ta_profile_id = next(t["id"] for t in teachers if t["user_id"] == ta_id)
    
    c_resp = client.post("/school/classes", json={"name": "Sec Class", "teacher_id": ta_profile_id, "start_date": "2023-01-01", "end_date": "2023-06-01"}, headers=t_headers)
    class_id = c_resp.json()["id"]
    
    a_resp = client.post("/school/assignments", json={"title": "Sec Asgn", "class_id": class_id, "teacher_id": ta_profile_id, "due_at": (datetime.now() + timedelta(days=1)).isoformat(), "level": 1}, headers=t_headers)
    assign_id = a_resp.json()["id"]
    
    return {
        "class_id": class_id,
        "assign_id": assign_id,
        "ta_profile_id": ta_profile_id,
        "token_ta": token_ta,
        "token_tb": token_tb,
        "token_st": token_st
    }

def test_anon_create_assignment_unauthorized(client: TestClient, security_setup):
    s = security_setup
    resp = client.post(
        "/school/assignments",
        json={"title": "Hack", "class_id": s["class_id"], "teacher_id": s["ta_profile_id"], "due_at": str(datetime.now()), "level": 1}
    )
    assert resp.status_code == 401

def test_student_create_assignment_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.post(
        "/school/assignments",
        json={"title": "Student Hack", "class_id": s["class_id"], "teacher_id": s["ta_profile_id"], "due_at": str(datetime.now()), "level": 1},
        headers={"Authorization": f"Bearer {s['token_st']}"}
    )
    assert resp.status_code == 403

def test_student_delete_assignment_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.delete(
        f"/school/assignments/{s['assign_id']}",
        headers={"Authorization": f"Bearer {s['token_st']}"}
    )
    assert resp.status_code == 403

def test_student_update_assignment_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.put(
        f"/school/assignments/{s['assign_id']}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {s['token_st']}"}
    )
    assert resp.status_code == 403

def test_teacher_update_other_teacher_assignment_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.put(
        f"/school/assignments/{s['assign_id']}",
        json={"title": "Stolen"},
        headers={"Authorization": f"Bearer {s['token_tb']}"}
    )
    assert resp.status_code == 403

def test_teacher_delete_other_teacher_assignment_forbidden(client: TestClient, security_setup):
    s = security_setup
    resp = client.delete(
        f"/school/assignments/{s['assign_id']}",
        headers={"Authorization": f"Bearer {s['token_tb']}"}
    )
    assert resp.status_code == 403
