from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.school import (
    Assignment,
    AssignmentQuestion,
    ChatLog,
    Class,
    Concept,
    Student,
    UnderstandingScore,
    class_students,
)
from app.schemas.analytics import (
    AssignmentAnalyticsRead,
    AssignmentScoreSummary,
    ClassAnalyticsRead,
    ConceptScoreSummary,
    QuestionScoreSummary,
    StudentAnalyticsRead,
    StudentScoreSummary,
)


def _get_student_assignment_scores(db: Session, student_id: int):
    return (
        db.query(
            UnderstandingScore.assignment_id.label("assignment_id"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .filter(UnderstandingScore.student_id == student_id)
        .group_by(UnderstandingScore.assignment_id)
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
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.desc())
        .first()
    )
    hardest_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.avg_score)
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


def _get_concept_scores_for_assignment(db: Session, assignment_id: int):
    return (
        db.query(
            Concept.id.label("concept_id"),
            Concept.name.label("concept_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(UnderstandingScore, UnderstandingScore.concept_id == Concept.id)
        .filter(UnderstandingScore.assignment_id == assignment_id)
        .group_by(Concept.id, Concept.name)
    )


def _get_question_scores_for_assignment(db: Session, assignment_id: int):
    return (
        db.query(
            AssignmentQuestion.id.label("question_id"),
            AssignmentQuestion.prompt.label("question_prompt"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(UnderstandingScore, UnderstandingScore.question_id == AssignmentQuestion.id)
        .filter(UnderstandingScore.assignment_id == assignment_id)
        .group_by(AssignmentQuestion.id, AssignmentQuestion.prompt)
    )


def get_assignment_analytics(db: Session, assignment_id: int) -> AssignmentAnalyticsRead:
    concept_scores = _get_concept_scores_for_assignment(db, assignment_id).subquery()
    question_scores = _get_question_scores_for_assignment(db, assignment_id).subquery()

    most_understood_concept = (
        db.query(concept_scores.c.concept_id, concept_scores.c.concept_name, concept_scores.c.avg_score)
        .order_by(concept_scores.c.avg_score.desc())
        .first()
    )
    least_understood_concept = (
        db.query(concept_scores.c.concept_id, concept_scores.c.concept_name, concept_scores.c.avg_score)
        .order_by(concept_scores.c.avg_score.asc())
        .first()
    )
    most_understood_question = (
        db.query(question_scores.c.question_id, question_scores.c.question_prompt, question_scores.c.avg_score)
        .order_by(question_scores.c.avg_score.desc())
        .first()
    )
    least_understood_question = (
        db.query(question_scores.c.question_id, question_scores.c.question_prompt, question_scores.c.avg_score)
        .order_by(question_scores.c.avg_score.asc())
        .first()
    )

    return AssignmentAnalyticsRead(
        assignment_id=assignment_id,
        most_understood_concept=ConceptScoreSummary.from_row(most_understood_concept),
        least_understood_concept=ConceptScoreSummary.from_row(least_understood_concept),
        most_understood_question=QuestionScoreSummary.from_row(most_understood_question),
        least_understood_question=QuestionScoreSummary.from_row(least_understood_question),
    )


def _get_class_student_ids(db: Session, class_id: int) -> list[int]:
    return [
        student.user_id
        for student in db.query(Student)
        .join(class_students, class_students.c.student_id == Student.id)
        .filter(class_students.c.class_id == class_id)
        .all()
    ]


def get_class_analytics(db: Session, class_id: int) -> ClassAnalyticsRead:
    student_user_ids = _get_class_student_ids(db, class_id)
    if not student_user_ids:
        return ClassAnalyticsRead(
            class_id=class_id,
            most_understood_assignment=None,
            least_understood_assignment=None,
            student_rankings=[],
        )

    assignment_scores = (
        db.query(
            UnderstandingScore.assignment_id.label("assignment_id"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
        .group_by(UnderstandingScore.assignment_id)
        .subquery()
    )

    most_understood_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.desc())
        .first()
    )
    least_understood_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.asc())
        .first()
    )

    student_rankings = (
        db.query(
            UnderstandingScore.student_id.label("student_id"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
        .group_by(UnderstandingScore.student_id)
        .order_by(func.avg(UnderstandingScore.score).desc())
        .all()
    )

    return ClassAnalyticsRead(
        class_id=class_id,
        most_understood_assignment=AssignmentScoreSummary.from_row(most_understood_assignment),
        least_understood_assignment=AssignmentScoreSummary.from_row(least_understood_assignment),
        student_rankings=[
            StudentScoreSummary(student_id=row.student_id, average_score=row.avg_score)
            for row in student_rankings
        ],
    )


def ensure_assignment_exists(db: Session, assignment_id: int) -> Assignment | None:
    return db.get(Assignment, assignment_id)


def ensure_class_exists(db: Session, class_id: int) -> Class | None:
    return db.get(Class, class_id)
