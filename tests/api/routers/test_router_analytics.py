from fastapi.testclient import TestClient
from datetime import date, datetime
from app.models.school import UnderstandingScore

def test_analytics_endpoints(client: TestClient, db_session):
    # 1. Setup: Register Teacher & Student
    # Teacher
    client.post("/auth/register", json={"email": "an_teacher@school.com", "password": "pw", "first_name": "A", "last_name": "T", "is_teacher": True})
    # Login Teacher
    t_login = client.post("/auth/token", data={"username": "an_teacher@school.com", "password": "pw"})
    t_token = t_login.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}
    
    # Get Teacher ID
    t_user_id = client.get("/auth/users/me/", headers=t_headers).json()["id"]
    teacher_id = next(t["id"] for t in client.get("/school/teachers").json() if t["user_id"] == t_user_id)

    # Student
    client.post("/auth/register", json={"email": "an_student@school.com", "password": "pw", "first_name": "A", "last_name": "S", "is_teacher": False})
    # Login Student
    s_login = client.post("/auth/token", data={"username": "an_student@school.com", "password": "pw"})
    s_token = s_login.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    s_user_id = client.get("/auth/users/me/", headers=s_headers).json()["id"]
    student_id = next(s["id"] for s in client.get("/school/students").json() if s["user_id"] == s_user_id)

    # 2. Setup: Create Class & Assignment (Authenticated as Teacher)
    c_resp = client.post(
        "/school/classes", 
        json={
            "name": "Analytics 101", 
            "teacher_id": teacher_id, 
            "start_date": str(date.today()), 
            "end_date": str(date.today()), 
            "period": "1"
        },
        headers=t_headers
    )
    assert c_resp.status_code == 201
    class_id = c_resp.json()["id"]
    join_code = c_resp.json()["join_code"]

    a_resp = client.post(
        "/school/assignments", 
        json={
            "title": "Data Mining", 
            "class_id": class_id, 
            "teacher_id": teacher_id, 
            "due_at": str(datetime.now()), 
            "level": 4
        },
        headers=t_headers
    )
    assert a_resp.status_code == 201
    assign_id = a_resp.json()["id"]

    # Enroll Student (Join endpoint is public/unprotected for now)
    client.post("/school/classes/join", json={"join_code": join_code, "student_id": student_id})

    # Add a Score manually
    score = UnderstandingScore(
        student_id=student_id,
        assignment_id=assign_id,
        score=0.85,
        confidence=0.9,
        source="import"
    )
    db_session.add(score)
    db_session.commit()

    # 2. Test Get Student Analytics (Authenticated as Student)
    sa_resp = client.get(f"/analytics/students/{student_id}", headers=s_headers)
    assert sa_resp.status_code == 200
    sa_data = sa_resp.json()
    assert sa_data["student_id"] == student_id
    
    # 3. Test Get Assignment Analytics (Currently Public/Unprotected? or Teacher only?)
    # Currently unprotected in router.
    aa_resp = client.get(f"/analytics/assignments/{assign_id}")
    assert aa_resp.status_code == 200
    aa_data = aa_resp.json()
    assert aa_data["assignment_id"] == assign_id

    # 4. Test Get Class Analytics (Currently Public/Unprotected?)
    ca_resp = client.get(f"/analytics/classes/{class_id}")
    assert ca_resp.status_code == 200
    ca_data = ca_resp.json()
    assert ca_data["class_id"] == class_id
