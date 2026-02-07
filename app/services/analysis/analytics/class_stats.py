from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.school import (
    Assignment,
    Class,
    Student,
    UnderstandingScore,
    class_students,
)
from app.schemas.analytics import (
    AssignmentScoreSummary,
    ClassAnalyticsRead,
    StudentScoreSummary,
)
from .common import _calculate_weakness_groups_for_students

def _get_class_student_ids(db: Session, class_id: int) -> list[int]:
    return [
        student.user_id
        for student in db.query(Student)
        .join(class_students, class_students.c.student_id == Student.id)
        .filter(class_students.c.class_id == class_id)
        .all()
    ]


def ensure_class_exists(db: Session, class_id: int) -> Class | None:
    return db.get(Class, class_id)


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
            Assignment.title.label("assignment_title"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Assignment, Assignment.id == UnderstandingScore.assignment_id)
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
        .filter(Assignment.class_id == class_id)
        .group_by(UnderstandingScore.assignment_id, Assignment.title)
        .subquery()
    )

    most_understood_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.assignment_title, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.desc())
        .first()
    )
    least_understood_assignment = (
        db.query(assignment_scores.c.assignment_id, assignment_scores.c.assignment_title, assignment_scores.c.avg_score)
        .order_by(assignment_scores.c.avg_score.asc())
        .first()
    )

    student_rankings = (
        db.query(
            UnderstandingScore.student_id.label("student_id"),
            Student.name.label("student_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Student, Student.user_id == UnderstandingScore.student_id)
        .join(Assignment, Assignment.id == UnderstandingScore.assignment_id)
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
        .filter(Assignment.class_id == class_id)
        .group_by(UnderstandingScore.student_id, Student.name)
        .order_by(func.avg(UnderstandingScore.score).desc())
        .all()
    )

    # Calculate Weakness Groups early for status logic
    weakness_groups = _calculate_weakness_groups_for_students(db, student_user_ids, class_id=class_id)

    # Calculate Overall Class Status
    overall_avg_score = 0.0
    if student_rankings:
        # Simple Average of students averages
        total_score = sum(s.avg_score for s in student_rankings)
        overall_avg_score = total_score / len(student_rankings)

    status_text = "Class Performing Well"
    status_color = "text-green-500" 
    
    if overall_avg_score >= 0.8:
        status_text = "Your class is excelling. Understanding is high."
        status_color = "text-green-600"
    elif overall_avg_score >= 0.7:
        status_text = "Your class is doing well, but room for improvement."
        status_color = "text-blue-600"
    elif overall_avg_score >= 0.6:
        status_text = "Your class performance is average. Review concepts."
        status_color = "text-yellow-600"
    else:
        status_text = "Your class is struggling. Immediate attention required."
        status_color = "text-red-600"

    # Refine message if specific weakness
    if weakness_groups and overall_avg_score < 0.7:
        top_weakness = weakness_groups[0]
        status_text = f"Your class is struggling with {top_weakness.concept_name}."


    return ClassAnalyticsRead(
        class_id=class_id,
        most_understood_assignment=AssignmentScoreSummary.from_row(most_understood_assignment),
        least_understood_assignment=AssignmentScoreSummary.from_row(least_understood_assignment),
        student_rankings=[
            StudentScoreSummary(student_id=row.student_id, student_name=row.student_name, average_score=row.avg_score)
            for row in student_rankings
        ],
        weakness_groups=weakness_groups,
        class_status=status_text,
        class_status_color=status_color,
    )
