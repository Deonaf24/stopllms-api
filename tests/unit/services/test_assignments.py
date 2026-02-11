from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from app.services.auth import create_user
from app.services.school.classes import create_class
from app.services.school.assignments import create_assignment, update_assignment, delete_assignment, get_assignment
from app.schemas.auth import UserCreate
from app.schemas.school import ClassCreate, AssignmentCreate, AssignmentUpdate

def test_assignment_lifecycle(db_session: Session):
    # 1. Setup: Create Teacher and Class
    user = create_user(db_session, UserCreate(email="t3@school.com", password="pw", first_name="T", last_name="Three", is_teacher=True))
    teacher = user.teacher_link
    
    class_in = ClassCreate(name="Science 101", teacher_id=teacher.id, start_date=date.today(), end_date=date.today())
    new_class = create_class(db_session, class_in)

    # 2. Create Assignment
    due_date = datetime.now() + timedelta(days=7)
    assign_in = AssignmentCreate(
        title="Lab Report",
        description="Write about gravity",
        class_id=new_class.id,
        teacher_id=teacher.id,
        due_at=due_date,
        level=1
    )
    assignment = create_assignment(db_session, assign_in)
    
    assert assignment.id is not None
    assert assignment.title == "Lab Report"
    assert assignment.class_id == new_class.id

    # 3. Update Assignment
    update_in = AssignmentUpdate(title="Physics Lab Report")
    updated = update_assignment(db_session, assignment.id, update_in)
    
    assert updated.title == "Physics Lab Report"
    assert updated.description == "Write about gravity" # Unchanged

    # 4. Delete Assignment
    deleted = delete_assignment(db_session, assignment.id)
    assert deleted.id == assignment.id
    
    # 5. Verify Deletion
    assert get_assignment(db_session, assignment.id) is None
