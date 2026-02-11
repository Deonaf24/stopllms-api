from fastapi.testclient import TestClient
from datetime import date

def test_create_class_and_join(client: TestClient):
    # 1. Register Teacher
    t_resp = client.post(
        "/auth/register",
        json={
            "email": "class_teacher@school.com",
            "password": "pw",
            "first_name": "Class",
            "last_name": "Teacher",
            "is_teacher": True
        }
    )
    assert t_resp.status_code == 200
    teacher_user_id = t_resp.json()["id"]

    # Login Teacher
    login_resp = client.post(
        "/auth/token",
        data={"username": "class_teacher@school.com", "password": "pw"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1a. Get Teacher Profile ID
    teachers = client.get("/school/teachers").json()
    my_teacher = next(t for t in teachers if t["user_id"] == teacher_user_id)
    teacher_id = my_teacher["id"]

    # 2. Create Class (Authenticated)
    class_payload = {
        "name": "Integration Test 101",
        "teacher_id": teacher_id,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "period": "1",
        "description": "Test Class"
    }
    c_resp = client.post("/school/classes", json=class_payload, headers=headers)
    assert c_resp.status_code == 201
    class_data = c_resp.json()
    assert class_data["name"] == "Integration Test 101"
    assert class_data["join_code"] is not None
    join_code = class_data["join_code"]

    # 3. Register Student
    s_resp = client.post(
        "/auth/register",
        json={
            "email": "class_student@school.com",
            "password": "pw",
            "first_name": "Class",
            "last_name": "Student",
            "is_teacher": False
        }
    )
    assert s_resp.status_code == 200
    student_user_id = s_resp.json()["id"]
    
    # 3a. Get Student Profile ID
    students = client.get("/school/students").json()
    my_student = next(s for s in students if s["user_id"] == student_user_id)
    student_id = my_student["id"]

    # 4. Join Class
    # (Currently join endpoint is public/unprotected in terms of auth header, though it requires valid IDs)
    # We will test it as is.
    join_resp = client.post(
        "/school/classes/join",
        json={
            "join_code": join_code,
            "student_id": student_id
        }
    )
    assert join_resp.status_code == 200
    updated_class = join_resp.json()
    assert updated_class["id"] == class_data["id"]
