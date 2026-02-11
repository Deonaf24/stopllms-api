from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.school import (
    Chapter,
    UnderstandingScore,
)
from app.schemas.analytics import (
    ChapterAnalyticsRead,
    ConceptScoreNode,
)
from .student import _get_concept_scores_for_student
from .class_stats import _get_class_student_ids

def get_chapter_analytics(db: Session, class_id: int, student_id: int) -> list[ChapterAnalyticsRead]:
    # 1. Fetch global concept scores for the student
    # This returns rows: (concept_id, concept_name, avg_score)
    scores_query = _get_concept_scores_for_student(db, student_id).all()
    score_map = {row.concept_id: float(row.avg_score) for row in scores_query}

    # 2. Fetch Chapters for the class, eagerly loading concepts
    # We join chapter_concepts to filter or just lazy load. 
    # Since we need concepts, we can rely on lazy loading or options(joinedload(Chapter.concepts))
    chapters = db.query(Chapter).filter(Chapter.class_id == class_id).order_by(Chapter.order).all()

    results = []
    
    for chapter in chapters:
        concept_nodes = []
        total_chapter_score = 0.0
        scored_concepts_count = 0

        # Unique concepts in chapter
        # Chapter.concepts is a list of Concept objects
        for concept in chapter.concepts:
            score = score_map.get(concept.id, 0.0)
            
            # If the student hasn't attempted it, score is 0. 
            # Should we count 0s in the average? 
            # - If they haven't started, their "Mastery" is 0. So yes.
            # - Or should we only average "attempted" concepts?
            # User request: "Understanding score". Usually implies mastery of the material.
            # So 0 is appropriate if unattempted.
            
            concept_nodes.append(ConceptScoreNode(
                concept_id=concept.id,
                concept_name=concept.name,
                understanding_score=score
            ))
            
            total_chapter_score += score
            scored_concepts_count += 1
        
        # Calculate Chapter Average
        # Avoid division by zero
        chapter_avg = 0.0
        if scored_concepts_count > 0:
            chapter_avg = total_chapter_score / scored_concepts_count
            
        results.append(ChapterAnalyticsRead(
            chapter_id=chapter.id,
            chapter_title=chapter.title,
            understanding_score=chapter_avg,
            concepts=concept_nodes
        ))
        
    return results


def get_class_chapter_stats(db: Session, class_id: int) -> list[ChapterAnalyticsRead]:
    # 1. Get all student IDs in the class
    student_ids = _get_class_student_ids(db, class_id)
    if not student_ids:
        # No students -> No scores. Return structure with 0s?
        # Or returns empty if we want. But structure with 0s is better for "Course Content" view.
        # Let's verify if we should just return empty or 0-filled. 
        # Ideally we fetch chapters anyway.
        pass

    # 2. Fetch Class-Wide Concept Averages
    # Query: Average score per concept for ALL students in this class
    # We filter by student_ids.
    score_map = {}
    if student_ids:
        avg_scores_query = (
            db.query(
                UnderstandingScore.concept_id, 
                func.avg(UnderstandingScore.score).label("avg_score")
            )
            .filter(UnderstandingScore.student_id.in_(student_ids))
            .group_by(UnderstandingScore.concept_id)
            .all()
        )
        score_map = {row.concept_id: float(row.avg_score) for row in avg_scores_query}

    # 3. Fetch Chapters
    chapters = db.query(Chapter).filter(Chapter.class_id == class_id).order_by(Chapter.order).all()

    results = []
    
    for chapter in chapters:
        concept_nodes = []
        total_chapter_score = 0.0
        scored_concepts_count = 0

        for concept in chapter.concepts:
            # Class average for this concept. 0.0 if no one touched it.
            score = score_map.get(concept.id, 0.0)
            
            concept_nodes.append(ConceptScoreNode(
                concept_id=concept.id,
                concept_name=concept.name,
                understanding_score=score
            ))
            
            total_chapter_score += score
            scored_concepts_count += 1
        
        chapter_avg = 0.0
        if scored_concepts_count > 0:
            chapter_avg = total_chapter_score / scored_concepts_count
            
        results.append(ChapterAnalyticsRead(
            chapter_id=chapter.id,
            chapter_title=chapter.title,
            understanding_score=chapter_avg,
            concepts=concept_nodes
        ))
        
    return results
