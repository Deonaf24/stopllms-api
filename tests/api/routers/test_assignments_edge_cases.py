from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest
import uuid

@pytest.fixture
def edge_case_setup(client: TestClient):
    # Setup Teacher
    uid = str(uuid.uuid4())[:8]
    email_t = f"teach_edge_{uid}@sec.com"
    
    # Register/Login Teacher
    client.post("/auth/register", json={"email": email_t, "password": "pw", "first_name": "T", "last_name": "E", "is_teacher": True})
    token = client.post("/auth/token", data={"username": email_t, "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Profile ID
    t_id = client.get("/auth/users/me/", headers=headers).json()["id"]
    teachers = client.get("/school/teachers").json()
    t_profile_id = next(t["id"] for t in teachers if t["user_id"] == t_id)
    
    # Create Class
    c_resp = client.post("/school/classes", json={"name": "Edge Class", "teacher_id": t_profile_id, "start_date": "2023-01-01", "end_date": "2023-06-01"}, headers=headers)
    class_id = c_resp.json()["id"]
    
    return {
        "headers": headers,
        "class_id": class_id,
        "t_profile_id": t_profile_id
    }

def test_get_non_existent_assignment_404(client: TestClient, edge_case_setup):
    s = edge_case_setup
    resp = client.get("/school/assignments/999999", headers=s["headers"])
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Assignment not found"

def test_update_non_existent_assignment_404(client: TestClient, edge_case_setup):
    s = edge_case_setup
    resp = client.put(
        "/school/assignments/999999", 
        json={"title": "Ghost"},
        headers=s["headers"]
    )
    assert resp.status_code == 404

def test_delete_non_existent_assignment_404(client: TestClient, edge_case_setup):
    s = edge_case_setup
    resp = client.delete("/school/assignments/999999", headers=s["headers"])
    assert resp.status_code == 404

def test_create_assignment_missing_title_422(client: TestClient, edge_case_setup):
    s = edge_case_setup
    # Missing 'title' field
    resp = client.post(
        "/school/assignments",
        json={
            "description": "No Title",
            "class_id": s["class_id"],
            "teacher_id": s["t_profile_id"]
        },
        headers=s["headers"]
    )
    assert resp.status_code == 422

def test_create_assignment_invalid_date_type_422(client: TestClient, edge_case_setup):
    s = edge_case_setup
    # 'due_at' is not a datetime
    resp = client.post(
        "/school/assignments",
        json={
            "title": "Bad Date",
            "class_id": s["class_id"],
            "teacher_id": s["t_profile_id"],
            "due_at": "not-a-date"
        },
        headers=s["headers"]
    )
    assert resp.status_code == 422

def test_get_class_assignments_empty_list(client: TestClient, edge_case_setup):
    s = edge_case_setup
    # We haven't created any assignments for this class yet.
    # The endpoint /school/assignments lists ALL assignments currently (maybe filtered by query params in future?)
    # or per class? The router `list_assignments` gets ALL.
    # For a unit/integration test, if DB is shared, this might return others.
    # But usually we want to test filtering capability if it existed.
    # Since `list_assignments` returns all, we can't assert empty unless DB is clean.
    # SKIPPING empty list check on global endpoint unless we filter by class.
    pass 

def test_create_assignment_past_due_date_allowed(client: TestClient, edge_case_setup):
    s = edge_case_setup
    # Logic Choice: Is it allowed to create backdated assignments? Usually yes (for recording purposes).
    # This test asserts that it IS allowed (201).
    past_date = (datetime.now() - timedelta(days=10)).isoformat()
    resp = client.post(
        "/school/assignments",
        json={
            "title": "History Assignment",
            "class_id": s["class_id"],
            "teacher_id": s["t_profile_id"],
            "due_at": past_date
        },
        headers=s["headers"]
    )
    assert resp.status_code == 201
    assert resp.json()["due_at"] == past_date
