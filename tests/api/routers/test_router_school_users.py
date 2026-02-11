from fastapi.testclient import TestClient

def test_create_and_get_teacher(client: TestClient):
    # 1. Create Teacher
    response = client.post(
        "/school/teachers",
        json={
            "name": "Mr. API",
            "email": "api_teacher@school.com",
            # We need a user_id. Does the endpoint require it?
            # Let's check schema TeacherCreate. It likely needs user_id or creates one?
            # The service creates a teacher profile linked to a user.
            # But wait, `create_teacher` in `services/school/users.py` takes `TeacherCreate`.
            # `TeacherCreate` schema probably has `user_id`.
            # If so, we need a user first.
            # But the endpoint `create_teacher` takes `TeacherCreate`.
            # Typically you register a user (Auth) then create a profile if it wasn't automatic.
            # Or this endpoint is for admins to create teachers directly? 
            # If `TeacherCreate` requires `user_id`, we must create a user first.
        }
    )
    # Checking schema or router code: users_service.create_teacher takes TeacherCreate
    # Let's look at invalid input to see what happens or assume we need a user.
    # Actually, let's create a user first via auth, then try to create a teacher profile for them manually?
    # But `auth.create_user` automatically creates a profile if `is_teacher=True`.
    # So `auth` registration is the primary way. The `/school/teachers` POST might be for subsequent profile creation or admin usage.
    # Let's verify `GET /school/teachers` works after `auth/register`
    
    # 1. Register as teacher via Auth
    reg_response = client.post(
        "/auth/register",
        json={
            "email": "school_teacher@test.com",
            "password": "pw",
            "first_name": "School",
            "last_name": "Teacher",
            "is_teacher": True
        }
    )
    assert reg_response.status_code == 200
    user_id = reg_response.json()["id"]

    # 2. List Teachers to find the new one
    list_response = client.get("/school/teachers")
    assert list_response.status_code == 200
    teachers = list_response.json()
    my_teacher = next((t for t in teachers if t["user_id"] == user_id), None)
    assert my_teacher is not None
    assert my_teacher["email"] == "school_teacher@test.com"

    # 3. Get Specific Teacher
    get_response = client.get(f"/school/teachers/{my_teacher['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "School Teacher"

def test_create_and_get_student(client: TestClient):
    # 1. Register as student via Auth
    reg_response = client.post(
        "/auth/register",
        json={
            "email": "school_student@test.com",
            "password": "pw",
            "first_name": "School",
            "last_name": "Student",
            "is_teacher": False
        }
    )
    assert reg_response.status_code == 200
    user_id = reg_response.json()["id"]

    # 2. List Students
    list_response = client.get("/school/students")
    assert list_response.status_code == 200
    students = list_response.json()
    my_student = next((s for s in students if s["user_id"] == user_id), None)
    assert my_student is not None
    assert my_student["email"] == "school_student@test.com"
