from fastapi.testclient import TestClient
import pytest
import uuid

@pytest.fixture
def analytics_edge_setup(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    email_t = f"t_an_edge_{uid}@test.com"

    # Register Teacher
    client.post("/auth/register", json={"email": email_t, "password": "pw", "first_name": "T", "last_name": "E", "is_teacher": True})
    token_t = client.post("/auth/token", data={"username": email_t, "password": "pw"}).json()["access_token"]

    return {
        "headers_t": {"Authorization": f"Bearer {token_t}"}
    }

def test_get_analytics_non_existent_student_404(client: TestClient, analytics_edge_setup):
    s = analytics_edge_setup
    # Teacher requests analytics for student ID 999999
    # Service layer (analytics_service.get_student_analytics) usually queries Student.
    # If Student not found, it might return empty or raise 404.
    # Let's verify expected behavior. Ideally 404 if the student doesn't exist.
    resp = client.get("/analytics/students/999999", headers=s["headers_t"])
    
    # If the endpoint returns empty data (200) instead of 404, we might need to adjust expectation or code.
    # But usually 404 is better for "RESOURCE not found".
    # Let's assert 404 first.
    assert resp.status_code == 404

def test_get_analytics_non_existent_assignment_404(client: TestClient, analytics_edge_setup):
    s = analytics_edge_setup
    resp = client.get("/analytics/assignments/999999", headers=s["headers_t"])
    assert resp.status_code == 404

def test_get_analytics_non_existent_class_404(client: TestClient, analytics_edge_setup):
    s = analytics_edge_setup
    resp = client.get("/analytics/classes/999999", headers=s["headers_t"])
    assert resp.status_code == 404
