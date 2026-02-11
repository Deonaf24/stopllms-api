from datetime import datetime, timezone
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.analytics import (
    AssignmentQuestionRead,
    AssignmentStructureReviewRead,
    ConceptRead,
    UnderstandingScoreRead,
)


def test_concept_read_schema():
    now = datetime.now(timezone.utc)
    concept = ConceptRead(id=1, name="Vectors", description="Vector math", created_at=now, updated_at=now)
    assert concept.id == 1
    assert concept.name == "Vectors"


def test_assignment_question_read_schema():
    now = datetime.now(timezone.utc)
    question = AssignmentQuestionRead(
        id=10,
        assignment_id=7,
        prompt="Solve for x",
        position=1,
        concept_ids=[1, 2],
        created_at=now,
        updated_at=now,
    )
    assert question.assignment_id == 7
    assert question.concept_ids == [1, 2]


def test_understanding_score_read_schema():
    now = datetime.now(timezone.utc)
    score = UnderstandingScoreRead(
        id=5,
        student_id=3,
        assignment_id=9,
        question_id=2,
        concept_id=4,
        score=0.75,
        confidence=0.6,
        source="ollama",
        created_at=now,
        updated_at=now,
    )
    assert score.score == 0.75
    assert score.source == "ollama"


def test_assignment_structure_review_read_schema():
    review = AssignmentStructureReviewRead(
        assignment_id=42,
        concepts=[{"id": 1, "name": "Linear equations"}],
        questions=[{"id": 3, "prompt": "Solve x+2=4", "concept_ids": [1]}],
        question_concepts=[{"question_id": 3, "concept_id": 1}],
        assignment_concepts=[{"concept_id": 1}],
        structure_approved=True,
    )
    assert review.structure_approved is True
    assert review.questions[0].concept_ids == [1]
