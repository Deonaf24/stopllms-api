from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.school import UnderstandingScore, Concept

def get_student_learning_summary(db: Session, student_id: int) -> str | None:
    """
    Generates a brief summary of the student's learning status based on UnderstandingScores,
    specifically focusing on Live Session performance to add context.
    """
    
    # Fetch recent scores
    # Group by Concept
    stats = (
        db.query(
            Concept.name,
            func.avg(UnderstandingScore.score).label("avg_score"),
            func.count(UnderstandingScore.id).label("count")
        )
        .join(Concept, Concept.id == UnderstandingScore.concept_id)
        .filter(UnderstandingScore.student_id == student_id)
        .group_by(Concept.name)
        .all()
    )
    
    if not stats:
        return None
        
    # Categorize
    strong = []
    weak = []
    
    for name, score, count in stats:
        if score >= 0.8:
            strong.append(f"{name} ({int(score*100)}%)")
        elif score < 0.6:
            weak.append(f"{name} ({int(score*100)}%)")
            
    summary_parts = []
    if strong:
        summary_parts.append(f"Strengths: {', '.join(strong)}.")
    if weak:
        summary_parts.append(f"Weaknesses: {', '.join(weak)}.")
        
    if not summary_parts:
        return "Student has average understanding of covered topics."
        
    return "Student Learning Context: " + " ".join(summary_parts)

def get_class_learning_summary(db: Session, class_id: int) -> str | None:
    """
    Generates a brief summary of the class's learning status based on aggregated UnderstandingScores.
    """
    
    # Fetch aggregated scores for the class
    # Join Assignment -> Class to filter by class_id
    from app.models.school import Assignment
    
    stats = (
        db.query(
            Concept.name,
            func.avg(UnderstandingScore.score).label("avg_score"),
            func.count(UnderstandingScore.id).label("count")
        )
        .join(Concept, Concept.id == UnderstandingScore.concept_id)
        .join(Assignment, Assignment.id == UnderstandingScore.assignment_id)
        .filter(Assignment.class_id == class_id)
        .group_by(Concept.name)
        .all()
    )
    
    if not stats:
        return None
        
    strong = []
    weak = []
    
    for name, score, count in stats:
        if score >= 0.8:
            strong.append(f"{name} ({int(score*100)}%)")
        elif score < 0.6:
            weak.append(f"{name} ({int(score*100)}%)")
            
    summary_parts = []
    if strong:
        summary_parts.append(f"Strengths: {', '.join(strong)}.")
    if weak:
        summary_parts.append(f"Weaknesses: {', '.join(weak)}.")
        
    if not summary_parts:
        return "Class has average understanding of covered topics."
        
    return "Class Context: " + " ".join(summary_parts)
