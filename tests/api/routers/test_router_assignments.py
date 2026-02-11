from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta

def test_assignment_crud_api(client: TestClient):
    # 1. Register Teacher
    client.post(
        "/auth/register",
        json={
            "email": "asgn_teacher@school.com",
            "password": "pw",
            "first_name": "Asgn",
            "last_name": "Teacher",
            "is_teacher": True
        }
    )
    # Login to get valid token
    login_resp = client.post(
        "/auth/token",
        data={"username": "asgn_teacher@school.com", "password": "pw"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Teacher ID
    teachers = client.get("/school/teachers").json()
    teacher_id = next(t["id"] for t in teachers if t["email"] == "asgn_teacher@school.com")

    # 2. Create Class
    # (Classes router is currently unprotected, but let's use headers for good measure just in case)
    c_resp = client.post(
        "/school/classes", 
        json={
            "name": "Asgn Class",
            "teacher_id": teacher_id,
            "start_date": str(date.today()),
            "end_date": str(date.today()),
            "period": "1"
        },
        headers=headers 
    )
    assert c_resp.status_code == 201
    class_id = c_resp.json()["id"]

    # 3. Create Assignment (Authenticted)
    due_at = (datetime.now() + timedelta(days=1)).isoformat()
    a_resp = client.post(
        "/school/assignments",
        json={
            "title": "API Test Assignment",
            "description": "Created via API",
            "class_id": class_id,
            "teacher_id": teacher_id,
            "due_at": due_at,
            "level": 3
        },
        headers=headers
    )
    assert a_resp.status_code == 201
    assignment = a_resp.json()
    assign_id = assignment["id"]
    assert assignment["title"] == "API Test Assignment"

    # 4. Get Assignment (Authenticated)
    get_resp = client.get(f"/school/assignments/{assign_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "API Test Assignment"

    # 5. Update Assignment (Authenticated)
    u_resp = client.put(
        f"/school/assignments/{assign_id}",
        json={"title": "Updated API Title"},
        headers=headers 
    )
    assert u_resp.status_code == 200
    assert u_resp.json()["title"] == "Updated API Title"

    # 6. Delete Assignment (Authenticated)
    del_resp = client.delete(f"/school/assignments/{assign_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["id"] == assign_id

    # Verify deletion
    get_fail = client.get(f"/school/assignments/{assign_id}", headers=headers)
    assert get_fail.status_code == 404
