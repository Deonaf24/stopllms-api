from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from app.models.school import LiveSession, LiveResponse, UnderstandingScore, LiveQuestion, Concept
import logging

logger = logging.getLogger(__name__)

def process_live_session_results(db: Session, session_id: int):
    """
    Aggregates results from a Live Session and updates Understanding Scores.
    """
    logger.info(f"Processing analytics for session {session_id}")
    
    session = db.query(LiveSession).filter(LiveSession.id == session_id).first()
    if not session:
        return

    # 1. Fetch all responses for the session
    # Join Question to filter by session
    responses = (
        db.query(LiveResponse)
        .options(selectinload(LiveResponse.student)) # Eager load student to access user_id
        .join(LiveQuestion)
        .filter(LiveQuestion.session_id == session_id)
        .all()
    )
    
    # 2. Group by Student and Concept
    if not session.concept_ids:
        logger.warning(f"Session {session_id} has no concepts linked. Skipping UnderstandingScore update.")
        return

    # Group responses by student_id (Student.id)
    student_responses = {}
    for r in responses:
        if r.student_id not in student_responses:
            student_responses[r.student_id] = []
        student_responses[r.student_id].append(r)
        
    total_questions = len(session.questions)
    if total_questions == 0:
        return

    # For each student, calculate score and update UnderstandingScore for EACH concept
    for student_db_id, user_responses in student_responses.items():
        if not user_responses:
            continue
            
        # Get User ID (required for UnderstandingScore) from the Student relation
        user_id = user_responses[0].student.user_id
        
        correct_count = sum(1 for r in user_responses if r.is_correct)
        
        # simple score: decimal (0.0 to 1.0)
        raw_score = (correct_count / total_questions)
        
        # Create UnderstandingScore entries
        for concept_id in session.concept_ids:
            score_entry = UnderstandingScore(
                student_id=user_id, # Correctly using User ID
                assignment_id=None, 
                concept_id=concept_id,
                score=raw_score,
                confidence=0.5 + (0.05 * len(user_responses)), 
                source="live_session"
            )
            db.add(score_entry)
            
        logger.info(f"Student {student_db_id} (User {user_id}) Score: {raw_score}% on Concepts {session.concept_ids}")

    db.commit()
    logger.info("Analytics processing complete and saved.") 
