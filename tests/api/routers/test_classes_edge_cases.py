from fastapi.testclient import TestClient
from datetime import date, timedelta
import pytest
import uuid

@pytest.fixture
def class_edge_setup(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    email_t = f"t_edge_{uid}@cls.com"
    email_s = f"s_edge_{uid}@cls.com"

    # Teacher
    client.post("/auth/register", json={"email": email_t, "password": "pw", "first_name": "T", "last_name": "E", "is_teacher": True})
    token_t = client.post("/auth/token", data={"username": email_t, "password": "pw"}).json()["access_token"]
    
    # Student
    client.post("/auth/register", json={"email": email_s, "password": "pw", "first_name": "S", "last_name": "E", "is_teacher": False})
    token_s = client.post("/auth/token", data={"username": email_s, "password": "pw"}).json()["access_token"]
    
    # Get Profile IDs
    headers_t = {"Authorization": f"Bearer {token_t}"}
    t_id = client.get("/auth/users/me/", headers=headers_t).json()["id"]
    teachers = client.get("/school/teachers").json()
    t_profile_id = next(t["id"] for t in teachers if t["user_id"] == t_id)
    
    headers_s = {"Authorization": f"Bearer {token_s}"}
    s_id = client.get("/auth/users/me/", headers=headers_s).json()["id"]
    students = client.get("/school/students").json()
    s_profile_id = next(s["id"] for s in students if s["user_id"] == s_id)

    return {
        "headers_t": headers_t,
        "headers_s": headers_s,
        "t_profile_id": t_profile_id,
        "s_profile_id": s_profile_id
    }

def test_get_non_existent_class_404(client: TestClient, class_edge_setup):
    s = class_edge_setup
    # Assuming there's a GET /school/classes/{id} endpoint? 
    # Let's check router. Assuming yes.
    resp = client.get("/school/classes/999999", headers=s["headers_t"]) # Auth might be required
    assert resp.status_code == 404

def test_join_class_invalid_code_404(client: TestClient, class_edge_setup):
    s = class_edge_setup
    resp = client.post(
        "/school/classes/join",
        json={"join_code": "INVALID-CODE-123", "student_id": s["s_profile_id"]}
    )
    # Could be 404 (Class not found) or 400 (Invalid code). 
    # Service logic usually looks up class by code. If none, 404.
    assert resp.status_code == 404

def test_create_class_missing_name_422(client: TestClient, class_edge_setup):
    s = class_edge_setup
    resp = client.post(
        "/school/classes",
        json={
            "teacher_id": s["t_profile_id"],
            "start_date": str(date.today()),
            "end_date": str(date.today()),
            "period": "1"
        },
        headers=s["headers_t"]
    )
    assert resp.status_code == 422

def test_create_class_end_date_before_start_422(client: TestClient, class_edge_setup):
    s = class_edge_setup
    # This requires business logic validation. Pydantic schema doesn't auto-check cross-fields commonly without validators.
    # Check if logic exists. If NOT, this test might FAIL (return 201), revealing a bug/logic gap.
    start = date.today()
    end = start - timedelta(days=10)
    
    resp = client.post(
        "/school/classes",
        json={
            "name": "Time Travel Class",
            "teacher_id": s["t_profile_id"],
            "start_date": str(start),
            "end_date": str(end),
            "period": "1"
        },
        headers=s["headers_t"]
    )
    # If the backend is robust, it should reject this. 
    # If it returns 201, we found a logic gap. 
    # I'll assert 400 or 422. If it fails, I'll know to fix logic.
    if resp.status_code == 201:
        pytest.fail("Logic Gap: Server allowed End Date before Start Date")
    
    assert resp.status_code in [400, 422]
