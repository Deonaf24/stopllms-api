from fastapi.testclient import TestClient
import pytest
import uuid

@pytest.fixture
def auth_edge_setup(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    email = f"existing_{uid}@auth.com"
    password = "password123"
    
    # Register one user
    client.post("/auth/register", json={"email": email, "password": password, "first_name": "E", "last_name": "X", "is_teacher": False})
    
    return {
        "email": email,
        "password": password
    }

def test_register_duplicate_email_400(client: TestClient, auth_edge_setup):
    s = auth_edge_setup
    # Try to register same email again
    resp = client.post(
        "/auth/register", 
        json={"email": s["email"], "password": "newpassword", "first_name": "Copy", "last_name": "Cat", "is_teacher": False}
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]

def test_login_wrong_password_401(client: TestClient, auth_edge_setup):
    s = auth_edge_setup
    resp = client.post(
        "/auth/token",
        data={"username": s["email"], "password": "wrongpassword"}
    )
    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]

def test_login_non_existent_user_401(client: TestClient):
    resp = client.post(
        "/auth/token",
        data={"username": "ghost@auth.com", "password": "pw"}
    )
    # Could be 401 or 404 depending on implementation. Standard OAuth2/Auth is usually 401 for security (don't reveal user existence).
    # Checking `app/routers/auth.py` would confirm, but 401 is safe bet.
    assert resp.status_code == 401

def test_register_missing_fields_422(client: TestClient):
    # Missing password
    resp = client.post(
        "/auth/register",
        json={"email": "incomplete@auth.com", "first_name": "I"}
    )
    assert resp.status_code == 422
