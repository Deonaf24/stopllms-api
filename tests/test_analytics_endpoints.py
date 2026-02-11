from datetime import datetime, timezone
import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.db import get_db
from app.models.base import Base
from app.models.school import Assignment, AssignmentQuestion, ChatLog, Class, Concept, UnderstandingScore, User
from app.routers import analytics


def _setup_test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(analytics.router)
    app.dependency_overrides[get_db] = _override_get_db
    return app, SessionLocal


def test_student_analytics_endpoint_returns_summary():
    app, SessionLocal = _setup_test_app()
    db = SessionLocal()

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

    db.add(
        UnderstandingScore(
            student_id=student.id,
            assignment_id=assignment.id,
            question_id=question.id,
            concept_id=concept.id,
            score=0.9,
        )
    )
    db.add(ChatLog(student_id=student.id, assignment_id=assignment.id, question="Help?"))
    db.commit()

    client = TestClient(app)
    response = client.get(f"/analytics/students/{student.id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["student_id"] == student.id
    assert payload["questions_asked"] == 1
