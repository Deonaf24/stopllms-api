from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.school import (
    Assignment,
    Concept,
    Student,
    UnderstandingScore,
)
from app.schemas.analytics import (
    StudentScoreSummary,
    WeaknessGroup,
)

def _calculate_weakness_groups_for_students(db: Session, student_ids: list[int], class_id: int | None = None) -> list[WeaknessGroup]:
    """
    Shared logic to calculate weakness groups for a list of students across ALL their assignments/concepts.
    """
    if not student_ids:
        return []

    # 1. Fetch all student-concept scores for these students
    query = (
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
    )

    if class_id:
        query = query.join(Assignment, Assignment.id == UnderstandingScore.assignment_id).filter(Assignment.class_id == class_id)

    student_concept_scores = (
        query
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
