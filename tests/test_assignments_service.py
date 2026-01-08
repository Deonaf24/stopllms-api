from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.school import Assignment, AssignmentQuestion, Class, Concept
from app.services.assignments import list_assignment_concepts, list_assignment_questions


def test_list_assignment_questions_orders_by_position():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

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

    q2 = AssignmentQuestion(assignment_id=assignment.id, prompt="Second", position=2)
    q1 = AssignmentQuestion(assignment_id=assignment.id, prompt="First", position=1)
    q3 = AssignmentQuestion(assignment_id=assignment.id, prompt="No position", position=None)
    db.add_all([q2, q1, q3])
    db.commit()

    questions = list_assignment_questions(db, assignment.id)
    assert [q.prompt for q in questions][:2] == ["First", "Second"]


def test_list_assignment_concepts_returns_assignment_concepts():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
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

    concept = Concept(name="Gravity", description=None)
    assignment.concepts.append(concept)
    db.add(assignment)
    db.commit()

    concepts = list_assignment_concepts(db, assignment.id)
    assert len(concepts) == 1
    assert concepts[0].name == "Gravity"
