from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_register_user(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": "api_user@test.com",
            "password": "strongpassword",
            "first_name": "API",
            "last_name": "User",
            "is_teacher": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "api_user@test.com"
    assert "id" in data

def test_login_and_me(client: TestClient):
    # 1. Register
    email = "login_user@test.com"
    password = "password123"
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "first_name": "L", "last_name": "U", "is_teacher": False}
    )

    # 2. Login (FormData)
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get Me
    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == email
