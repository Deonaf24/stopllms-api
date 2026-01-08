from datetime import datetime, timezone
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.school import (
    Assignment,
    AssignmentQuestion,
    ChatLog,
    Class,
    Concept,
    Student,
    UnderstandingScore,
    User,
)
from app.services.analytics import get_assignment_analytics, get_class_analytics, get_student_analytics


def _build_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return SessionLocal()


def test_student_analytics_aggregates_scores_and_questions():
    db = _build_session()
    class_obj = Class(name="Math", description=None, teacher_id=None, join_code="ABC123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Homework",
        description=None,
        due_at=datetime.now(timezone.utc),
        class_id=class_obj.id,
        teacher_id=None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    student = User(username="student1", email="student@example.com", hashed_password="hash", disabled=False)
    db.add(student)
    db.commit()
    db.refresh(student)

    concept = Concept(name="Algebra", description="Equations")
    db.add(concept)
    db.commit()
    db.refresh(concept)

    question = AssignmentQuestion(assignment_id=assignment.id, prompt="Solve x+2=4", position=1)
    db.add(question)
    db.commit()
    db.refresh(question)

    db.add_all(
        [
            UnderstandingScore(
                student_id=student.id,
                assignment_id=assignment.id,
                question_id=question.id,
                concept_id=concept.id,
                score=0.9,
            )
        ]
    )
    db.add(ChatLog(student_id=student.id, assignment_id=assignment.id, question="Help?"))
    db.commit()

    analytics = get_student_analytics(db, student.id)
    assert analytics.questions_asked == 1
    assert analytics.easiest_assignment.assignment_id == assignment.id
    assert analytics.most_understood_concept.concept_id == concept.id


def test_assignment_analytics_returns_question_and_concept_scores():
    db = _build_session()
    class_obj = Class(name="Science", description=None, teacher_id=None, join_code="SCI123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Lab",
        description=None,
        due_at=datetime.now(timezone.utc),
        class_id=class_obj.id,
        teacher_id=None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    user = User(username="student2", email="student2@example.com", hashed_password="hash", disabled=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    concept = Concept(name="Gravity", description=None)
    db.add(concept)
    db.commit()
    db.refresh(concept)

    question = AssignmentQuestion(assignment_id=assignment.id, prompt="Explain gravity", position=1)
    db.add(question)
    db.commit()
    db.refresh(question)

    db.add(
        UnderstandingScore(
            student_id=user.id,
            assignment_id=assignment.id,
            question_id=question.id,
            concept_id=concept.id,
            score=0.4,
        )
    )
    db.commit()

    analytics = get_assignment_analytics(db, assignment.id)
    assert analytics.least_understood_concept.concept_id == concept.id
    assert analytics.least_understood_question.question_id == question.id


def test_class_analytics_ranks_students_and_assignments():
    db = _build_session()
    class_obj = Class(name="History", description=None, teacher_id=None, join_code="HIS123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Essay",
        description=None,
        due_at=datetime.now(timezone.utc),
        class_id=class_obj.id,
        teacher_id=None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    user_a = User(username="studentA", email="a@example.com", hashed_password="hash", disabled=False)
    user_b = User(username="studentB", email="b@example.com", hashed_password="hash", disabled=False)
    db.add_all([user_a, user_b])
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)

    student_a = Student(name="Student A", email="a@example.com", user_id=user_a.id)
    student_b = Student(name="Student B", email="b@example.com", user_id=user_b.id)
    db.add_all([student_a, student_b])
    db.commit()
    db.refresh(student_a)
    db.refresh(student_b)

    class_obj.students.extend([student_a, student_b])
    db.commit()

    db.add_all(
        [
            UnderstandingScore(
                student_id=user_a.id,
                assignment_id=assignment.id,
                score=0.8,
            ),
            UnderstandingScore(
                student_id=user_b.id,
                assignment_id=assignment.id,
                score=0.5,
            ),
        ]
    )
    db.commit()

    analytics = get_class_analytics(db, class_obj.id)
    assert analytics.most_understood_assignment.assignment_id == assignment.id
    assert analytics.student_rankings[0].student_id == user_a.id
