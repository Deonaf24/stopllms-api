import pytest
from sqlalchemy.orm import Session
from app.models.school import User, Student, Assignment, Class, Concept, UnderstandingScore, Teacher
from app.services.analysis.analytics.student import get_student_analytics

@pytest.fixture
def analytics_data_setup(db_session: Session):
    # 1. Setup Student
    user = User(email="data_test@school.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    student = Student(user_id=user.id, name="Data Student", email="data_test@school.com")
    db_session.add(student)
    
    # 2. Setup Teacher & Class (Required for Assignment)
    t_user = User(email="data_teach@school.com", hashed_password="pw")
    db_session.add(t_user)
    db_session.commit()
    teacher = Teacher(user_id=t_user.id, name="Data Teacher", email="data_teach@school.com")
    db_session.add(teacher)
    
    class_obj = Class(name="Data Class", teacher_id=teacher.id, join_code="DATA1")
    db_session.add(class_obj)
    db_session.commit() # Get IDs
    
    # 3. Setup Assignments and Concepts
    c_math = Concept(name="Math", description="Numbers")
    c_hist = Concept(name="History", description="Past")
    db_session.add_all([c_math, c_hist])
    
    a_easy = Assignment(title="Easy Quiz", class_id=class_obj.id, teacher_id=teacher.id, level=1)
    a_hard = Assignment(title="Hard Exam", class_id=class_obj.id, teacher_id=teacher.id, level=5)
    db_session.add_all([a_easy, a_hard])
    db_session.commit()
    
    return {
        "student_id": student.id,
        "a_easy": a_easy,
        "a_hard": a_hard,
        "c_math": c_math,
        "c_hist": c_hist
    }

def test_analytics_ranking_integrity(db_session: Session, analytics_data_setup):
    s = analytics_data_setup
    sid = s["student_id"]
    
    # 4. Add Scores
    # Easy Assignment: Scores 100, 90 -> Avg 95
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_easy"].id, score=100.0, concept_id=s["c_math"].id))
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_easy"].id, score=90.0, concept_id=s["c_math"].id))
    
    # Hard Assignment: Scores 50, 60 -> Avg 55
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_hard"].id, score=50.0, concept_id=s["c_hist"].id))
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_hard"].id, score=60.0, concept_id=s["c_hist"].id))
    
    db_session.commit()
    
    # 5. Verify Calculations via Service
    analytics = get_student_analytics(db_session, sid)
    
    # Check Easiest/Hardest Assignment
    assert analytics.easiest_assignment.assignment_title == "Easy Quiz"
    assert analytics.easiest_assignment.average_score == 95.0
    
    assert analytics.hardest_assignment.assignment_title == "Hard Exam"
    assert analytics.hardest_assignment.average_score == 55.0
    
    # Check Concepts
    # Math: 100, 90 -> 95
    # History: 50, 60 -> 55
    assert analytics.most_understood_concept.concept_name == "Math"
    assert analytics.most_understood_concept.average_score == 95.0
    
    assert analytics.least_understood_concept.concept_name == "History"
    assert analytics.least_understood_concept.average_score == 55.0

def test_analytics_precision_integrity(db_session: Session, analytics_data_setup):
    s = analytics_data_setup
    sid = s["student_id"]
    
    # Precision test: 1/3 = 33.333...
    # We want to ensure DB/Service handles floats reasonably.
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_easy"].id, score=10.0, concept_id=s["c_math"].id))
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_easy"].id, score=10.0, concept_id=s["c_math"].id))
    db_session.add(UnderstandingScore(student_id=sid, assignment_id=s["a_easy"].id, score=30.0, concept_id=s["c_math"].id))
    # Avg = (10+10+30)/3 = 50/3 = 16.666...
    
    db_session.commit()
    
    analytics = get_student_analytics(db_session, sid)
    
    # Pydantic schema might round it, or SQL might.
    # Service implementation uses `AssignmentScoreSummary.from_row`.
    # Let's check the result.
    avg = analytics.easiest_assignment.average_score
    assert 16.6 < avg < 16.7
