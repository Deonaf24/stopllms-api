from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.school import (
    Assignment,
    ChatLog,
    Concept,
    UnderstandingScore,
)
from app.schemas.analytics import (
    AssignmentScoreSummary,
    ConceptScoreSummary,
    StudentAnalyticsRead,
)

def _get_student_assignment_scores(db: Session, student_id: int):
    return (
        db.query(
            UnderstandingScore.assignment_id.label("assignment_id"),
            Assignment.title.label("assignment_title"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Assignment, Assignment.id == UnderstandingScore.assignment_id)
        .filter(UnderstandingScore.student_id == student_id)
        .group_by(UnderstandingScore.assignment_id, Assignment.title)
    )


def _get_concept_scores_for_student(db: Session, student_id: int):
    return (
        db.query(
            Concept.id.label("concept_id"),
            Concept.name.label("concept_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(UnderstandingScore, UnderstandingScore.concept_id == Concept.id)
        .filter(UnderstandingScore.student_id == student_id)
        .group_by(Concept.id, Concept.name)
    )


def get_student_analytics(db: Session, student_id: int) -> StudentAnalyticsRead:
    assignment_scores = _get_student_assignment_scores(db, student_id).subquery()

    easiest_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.assignment_title, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.desc())
        .first()
    )
    hardest_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.assignment_title, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.asc())
        .first()
    )

    concept_scores = _get_concept_scores_for_student(db, student_id).subquery()
    most_understood = (
        db.query(concept_scores.c.concept_id, concept_scores.c.concept_name, concept_scores.c.avg_score)
        .order_by(concept_scores.c.avg_score.desc())
        .first()
    )
    least_understood = (
        db.query(concept_scores.c.concept_id, concept_scores.c.concept_name, concept_scores.c.avg_score)
        .order_by(concept_scores.c.avg_score.asc())
        .first()
    )

    question_count = (
        db.query(func.count(ChatLog.id))
        .filter(ChatLog.student_id == student_id)
        .scalar()
    )

    return StudentAnalyticsRead(
        student_id=student_id,
        questions_asked=int(question_count or 0),
        easiest_assignment=AssignmentScoreSummary.from_row(easiest_assignment),
        hardest_assignment=AssignmentScoreSummary.from_row(hardest_assignment),
        most_understood_concept=ConceptScoreSummary.from_row(most_understood),
        least_understood_concept=ConceptScoreSummary.from_row(least_understood),
    )
