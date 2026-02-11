from sqlalchemy.orm import Session
from datetime import datetime, date
from app.services.auth import create_user
from app.services.school.classes import create_class, enroll_student
from app.services.school.assignments import create_assignment
from app.services.analysis.analytics.student import get_student_analytics
from app.schemas.auth import UserCreate
from app.schemas.school import ClassCreate, AssignmentCreate
from app.models.school import UnderstandingScore, ChatLog, Concept, Assignment

def test_get_student_analytics_aggregation(db_session: Session):
    # 1. Setup Actors
    tuser = create_user(db_session, UserCreate(email="ta@school.com", password="pw", first_name="T", last_name="A", is_teacher=True))
    suser = create_user(db_session, UserCreate(email="sa@school.com", password="pw", first_name="S", last_name="A", is_teacher=False))
    teacher = tuser.teacher_link
    student = suser.student_link

    # 2. Setup Class & Enrollment
    class_in = ClassCreate(name="Stats 101", teacher_id=teacher.id, start_date=date.today(), end_date=date.today())
    class_obj = create_class(db_session, class_in)
    enroll_student(db_session, class_obj, student)

    # 3. Setup Concepts
    c1 = Concept(name="Easy Concept", description="Simple")
    c2 = Concept(name="Hard Concept", description="Complex")
    db_session.add_all([c1, c2])
    db_session.commit()

    # 4. Setup Assignments
    a1_in = AssignmentCreate(title="Easy Asgn", class_id=class_obj.id, teacher_id=teacher.id, due_at=datetime.now(), level=1)
    a2_in = AssignmentCreate(title="Hard Asgn", class_id=class_obj.id, teacher_id=teacher.id, due_at=datetime.now(), level=5)
    a1 = create_assignment(db_session, a1_in)
    a2 = create_assignment(db_session, a2_in)

    # Link concepts to assignments manually if needed, or just link via scores implies usage
    # The analytics query joins UnderstandingScore -> Assignment and UnderstandingScore -> Concept
    # It does NOT strictly require the Assignment->Concept link for these stats, 
    # as it aggregates UnderstandingScore.score grouped by Assignment or Concept.

    # 5. Populate Scores (Student gets high on A1/C1, low on A2/C2)
    scores = [
        # High scores for A1 / C1
        UnderstandingScore(student_id=student.id, assignment_id=a1.id, concept_id=c1.id, score=0.9, confidence=0.8),
        UnderstandingScore(student_id=student.id, assignment_id=a1.id, concept_id=c1.id, score=1.0, confidence=0.9),
        
        # Low scores for A2 / C2
        UnderstandingScore(student_id=student.id, assignment_id=a2.id, concept_id=c2.id, score=0.2, confidence=0.3),
        UnderstandingScore(student_id=student.id, assignment_id=a2.id, concept_id=c2.id, score=0.3, confidence=0.4),
    ]
    db_session.add_all(scores)
    
    # 6. Populate Chat Logs
    logs = [
        ChatLog(student_id=student.id, assignment_id=a1.id, question="Q1"),
        ChatLog(student_id=student.id, assignment_id=a1.id, question="Q2"),
        ChatLog(student_id=student.id, assignment_id=a2.id, question="Q3"),
    ]
    db_session.add_all(logs)
    db_session.commit()

    # 7. Run Aggregation
    analytics = get_student_analytics(db_session, student.id)

    # 8. Verify
    assert analytics.questions_asked == 3
    
    # Easiest should be A1 (Avg ~0.95)
    assert analytics.easiest_assignment is not None
    assert analytics.easiest_assignment.assignment_title == "Easy Asgn"
    assert analytics.easiest_assignment.average_score > 0.9

    # Hardest should be A2 (Avg ~0.25)
    assert analytics.hardest_assignment is not None
    assert analytics.hardest_assignment.assignment_title == "Hard Asgn"
    assert analytics.hardest_assignment.average_score < 0.4

    # Most Understood Concept (C1)
    assert analytics.most_understood_concept is not None
    assert analytics.most_understood_concept.concept_name == "Easy Concept"

    # Least Understood Concept (C2)
    assert analytics.least_understood_concept is not None
    assert analytics.least_understood_concept.concept_name == "Hard Concept"
