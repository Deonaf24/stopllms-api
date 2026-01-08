from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.school import Assignment, Class
from app.schemas.analytics import AssignmentStructureReview
from app.services.assignment_analysis import apply_assignment_structure


def test_apply_assignment_structure_marks_approved_and_replaces_structure():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    class_obj = Class(name="Math", description=None, teacher_id=None, join_code="ABC123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Homework 1",
        description=None,
        due_at=datetime.now(timezone.utc),
        class_id=class_obj.id,
        teacher_id=None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    payload = AssignmentStructureReview(
        assignment_id=assignment.id,
        concepts=[{"name": "Algebra", "description": "Linear equations"}],
        questions=[{"prompt": "Solve x+1=2", "position": 1}],
        question_concepts=[],
        assignment_concepts=[],
    )

    response = apply_assignment_structure(db, assignment, payload)
    assert response.structure_approved is True
    assert len(response.questions) == 1
    assert response.questions[0].prompt == "Solve x+1=2"
    assert response.concepts[0].name == "Algebra"
