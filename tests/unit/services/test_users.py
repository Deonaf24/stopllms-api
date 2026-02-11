from sqlalchemy.orm import Session
from app.services.auth import create_user
from app.services.school.users import get_teacher, get_student, update_teacher
from app.schemas.auth import UserCreate
from app.schemas.school import TeacherUpdate

def test_teacher_profile_creation_and_retrieval(db_session: Session):
    # 1. Create User via Auth Service (which creates Teacher profile)
    email = "teacher@test.com"
    user_in = UserCreate(email=email, password="password", first_name="Mr", last_name="Teacher", is_teacher=True)
    user = create_user(db_session, user_in)
    
    # 2. Verify Teacher Profile exists via School Service
    assert user.teacher_link is not None
    teacher = get_teacher(db_session, user.teacher_link.id)
    assert teacher is not None
    assert teacher.email == email
    assert teacher.user_id == user.id

def test_update_teacher_profile(db_session: Session):
    # 1. Create User/Teacher
    email = "update@test.com"
    user_in = UserCreate(email=email, password="password", first_name="To", last_name="Update", is_teacher=True)
    user = create_user(db_session, user_in)
    teacher = user.teacher_link
    
    # 2. Update Teacher Profile
    new_name = "Updated Name"
    update_in = TeacherUpdate(name=new_name)
    updated_teacher = update_teacher(db_session, teacher, update_in)
    
    assert updated_teacher.name == new_name
    
    # 3. Verify persistence
    refetched = get_teacher(db_session, teacher.id)
    assert refetched.name == new_name

def test_student_profile_creation(db_session: Session):
    email = "student@test.com"
    user_in = UserCreate(email=email, password="password", first_name="Student", last_name="One", is_teacher=False)
    user = create_user(db_session, user_in)
    
    assert user.student_link is not None
    student = get_student(db_session, user.student_link.id)
    assert student is not None
    assert student.email == email
