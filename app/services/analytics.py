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
    WeaknessGroup,
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

    student_rankings = (
        db.query(
            UnderstandingScore.student_id.label("student_id"),
            Student.name.label("student_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Student, Student.user_id == UnderstandingScore.student_id)
        .filter(UnderstandingScore.assignment_id == assignment_id)
        .group_by(UnderstandingScore.student_id, Student.name)
        .order_by(func.avg(UnderstandingScore.score).desc())
        .all()
    )

    # Weakness Grouping Logic
    # 1. Fetch all student-concept scores for this assignment
    student_concept_scores = (
        db.query(
            Concept.id.label("concept_id"),
            Concept.name.label("concept_name"),
            UnderstandingScore.student_id.label("student_id"),
            Student.name.label("student_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Concept, Concept.id == UnderstandingScore.concept_id)
        .join(Student, Student.user_id == UnderstandingScore.student_id)
        .filter(UnderstandingScore.assignment_id == assignment_id)
        .group_by(Concept.id, Concept.name, UnderstandingScore.student_id, Student.name)
        .all()
    )

    # 2. Group by concept, filtering for < 60%
    weakness_map: dict[int, dict] = {} # concept_id -> {name, students: [], total_score}
    
    for row in student_concept_scores:
        if row.avg_score >= 0.6:
            continue
            
        cid = row.concept_id
        if cid not in weakness_map:
            weakness_map[cid] = {
                "concept_id": cid,
                "concept_name": row.concept_name,
                "students": [],
                "total_score": 0.0
            }
        
        weakness_map[cid]["students"].append(
            StudentScoreSummary(
                student_id=row.student_id,
                student_name=row.student_name,
                average_score=row.avg_score
            )
        )
        weakness_map[cid]["total_score"] += row.avg_score

    # 3. specific WeaknessGroup objects
    weakness_groups = []
    for cid, data in weakness_map.items():
        count = len(data["students"])
        if count == 0: 
            continue
        
        group_avg = data["total_score"] / count
        weakness_groups.append(
            WeaknessGroup(
                concept_id=data["concept_id"],
                concept_name=data["concept_name"],
                students=data["students"],
                average_score=group_avg
            )
        )

    # Sort by number of struggling students (descending), then by avg score (ascending - lowest first)
    weakness_groups.sort(key=lambda x: (len(x.students), -x.average_score), reverse=True)

    return AssignmentAnalyticsRead(
        assignment_id=assignment_id,
        most_understood_concept=ConceptScoreSummary.from_row(most_understood_concept),
        least_understood_concept=ConceptScoreSummary.from_row(least_understood_concept),
        most_understood_question=QuestionScoreSummary.from_row(most_understood_question),
        least_understood_question=QuestionScoreSummary.from_row(least_understood_question),
        student_rankings=[
            StudentScoreSummary(student_id=row.student_id, student_name=row.student_name, average_score=row.avg_score)
            for row in student_rankings
        ],
        weakness_groups=weakness_groups,
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
            Assignment.title.label("assignment_title"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Assignment, Assignment.id == UnderstandingScore.assignment_id)
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
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
        .filter(UnderstandingScore.student_id.in_(student_user_ids))
        .group_by(UnderstandingScore.student_id, Student.name)
        .order_by(func.avg(UnderstandingScore.score).desc())
        .all()
    )

    return ClassAnalyticsRead(
        class_id=class_id,
        most_understood_assignment=AssignmentScoreSummary.from_row(most_understood_assignment),
        least_understood_assignment=AssignmentScoreSummary.from_row(least_understood_assignment),
        student_rankings=[
            StudentScoreSummary(student_id=row.student_id, student_name=row.student_name, average_score=row.avg_score)
            for row in student_rankings
        ],
        weakness_groups=_calculate_weakness_groups_for_students(db, student_user_ids),
    )


def _calculate_weakness_groups_for_students(db: Session, student_ids: list[int]) -> list[WeaknessGroup]:
    """
    Shared logic to calculate weakness groups for a list of students across ALL their assignments/concepts.
    """
    if not student_ids:
        return []

    # 1. Fetch all student-concept scores for these students
    student_concept_scores = (
        db.query(
            Concept.id.label("concept_id"),
            Concept.name.label("concept_name"),
            UnderstandingScore.student_id.label("student_id"),
            Student.name.label("student_name"),
            func.avg(UnderstandingScore.score).label("avg_score"),
        )
        .join(Concept, Concept.id == UnderstandingScore.concept_id)
        .join(Student, Student.user_id == UnderstandingScore.student_id)
        .filter(UnderstandingScore.student_id.in_(student_ids))
        .group_by(Concept.id, Concept.name, UnderstandingScore.student_id, Student.name)
        .all()
    )

    # 2. Group by concept, filtering for < 60%
    weakness_map: dict[int, dict] = {} 
    
    for row in student_concept_scores:
        if row.avg_score >= 0.6:
            continue
            
        cid = row.concept_id
        if cid not in weakness_map:
            weakness_map[cid] = {
                "concept_id": cid,
                "concept_name": row.concept_name,
                "students": [],
                "total_score": 0.0
            }
        
        weakness_map[cid]["students"].append(
            StudentScoreSummary(
                student_id=row.student_id,
                student_name=row.student_name,
                average_score=row.avg_score
            )
        )
        weakness_map[cid]["total_score"] += row.avg_score

    # 3. Create WeaknessGroup objects
    weakness_groups = []
    for cid, data in weakness_map.items():
        count = len(data["students"])
        if count == 0: 
            continue
        
        group_avg = data["total_score"] / count
        weakness_groups.append(
            WeaknessGroup(
                concept_id=data["concept_id"],
                concept_name=data["concept_name"],
                students=data["students"],
                average_score=group_avg
            )
        )

    # Sort: most struggling students first
    weakness_groups.sort(key=lambda x: (len(x.students), -x.average_score), reverse=True)
    return weakness_groups


def ensure_assignment_exists(db: Session, assignment_id: int) -> Assignment | None:
    return db.get(Assignment, assignment_id)


def ensure_class_exists(db: Session, class_id: int) -> Class | None:
    return db.get(Class, class_id)
