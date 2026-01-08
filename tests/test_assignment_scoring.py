import asyncio
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.school import Assignment, AssignmentQuestion, ChatLog, Class, Concept, UnderstandingScore, User
from app.schemas.analytics import UnderstandingScoreRead
from app.services import analysis as assignment_analysis


def test_score_assignment_understanding_persists_scores():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    class_obj = Class(name="Math", description=None, teacher_id=None, join_code="ABC123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Homework 2",
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
    question.concepts.append(concept)
    db.add(question)
    db.commit()
    db.refresh(question)

    assignment.concepts.append(concept)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    chat_log = ChatLog(
        student_id=student.id,
        assignment_id=assignment.id,
        question="How do I solve x+2=4?",
    )
    db.add(chat_log)
    db.commit()

    def _fake_ollama_generate(prompt: str, model: str | None = None) -> str:
        return (
            '{"scores": [{"student_id": %d, "question_id": %d, "concept_id": %d, '
            '"score": 0.8, "confidence": 0.7, "source": "ollama"}]}'
        ) % (student.id, question.id, concept.id)

    assignment_analysis.ollama_generate = _fake_ollama_generate

    scores = asyncio.run(assignment_analysis.score_assignment_understanding(db, assignment))
    assert len(scores) == 1
    score = scores[0]
    score_schema = UnderstandingScoreRead(
        id=score.id,
        student_id=score.student_id,
        assignment_id=score.assignment_id,
        question_id=score.question_id,
        concept_id=score.concept_id,
        score=score.score,
        confidence=score.confidence,
        source=score.source,
        created_at=score.created_at,
        updated_at=score.updated_at,
    )
    assert score_schema.score == 0.8


def test_score_assignment_understanding_soft_fallback_keeps_existing_scores():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    class_obj = Class(name="Math", description=None, teacher_id=None, join_code="ABC123")
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)

    assignment = Assignment(
        title="Homework 3",
        description=None,
        due_at=datetime.now(timezone.utc),
        class_id=class_obj.id,
        teacher_id=None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    student = User(username="student2", email="student2@example.com", hashed_password="hash", disabled=False)
    db.add(student)
    db.commit()
    db.refresh(student)

    existing = UnderstandingScore(
        student_id=student.id,
        assignment_id=assignment.id,
        score=0.6,
    )
    db.add(existing)
    db.add(
        ChatLog(
            student_id=student.id,
            assignment_id=assignment.id,
            question="Need help?",
        )
    )
    db.commit()

    def _bad_ollama_generate(prompt: str, model: str | None = None) -> str:
        return "not json"

    assignment_analysis.ollama_generate = _bad_ollama_generate

    scores = asyncio.run(assignment_analysis.score_assignment_understanding(db, assignment))
    assert scores == []
    remaining = db.query(UnderstandingScore).filter(UnderstandingScore.assignment_id == assignment.id).all()
    assert len(remaining) == 1
