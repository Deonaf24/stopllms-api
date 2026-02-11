from sqlalchemy.orm import Session
from datetime import date
from app.services.auth import create_user
from app.services.school.classes import create_class, enroll_student, get_class_by_join_code
from app.schemas.auth import UserCreate
from app.schemas.school import ClassCreate

def test_create_class_and_enrollment(db_session: Session):
    # 1. Create Teacher
    temail = "t2@school.com"
    tuser = create_user(db_session, UserCreate(email=temail, password="pw", first_name="T", last_name="Two", is_teacher=True))
    teacher = tuser.teacher_link

    # 2. Create Class
    class_in = ClassCreate(
        name="Math 101", 
        description="Intro to Algebra", 
        teacher_id=teacher.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 1)
    )
    # create_class typically generates a join_code if not provided, or we provide one?
    # Let's assume it handles it or we need to pass it if schema requires it.
    # Checking schema or service logic is ideal, but assuming standard flow:
    new_class = create_class(db_session, class_in)
    
    assert new_class.id is not None
    assert new_class.join_code is not None
    assert new_class.teacher_id == teacher.id

    # 3. Create Student
    semail = "s2@school.com"
    suser = create_user(db_session, UserCreate(email=semail, password="pw", first_name="S", last_name="Two", is_teacher=False))
    student = suser.student_link

    # 4. Enroll Student
    # Simulating the flow: get class by join code, then enroll
    found_class = get_class_by_join_code(db_session, new_class.join_code)
    assert found_class is not None
    
    enrolled_class = enroll_student(db_session, found_class, student)
    assert enrolled_class is not None
    
    # 5. Verify Enrollment
    db_session.refresh(found_class)
    assert student in found_class.students
