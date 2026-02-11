from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.db import get_db
from app.services.school import live_events as live_service
from app.schemas.live_events import LiveSession, LiveAnswerRequest, LiveAnswerResponse, LiveQuestion, LiveStatsResponse, LiveDashboardStats

router = APIRouter(prefix="/live", tags=["live"])

@router.post("/{session_id}/start", response_model=LiveSession)
def start_session(session_id: int, db: Session = Depends(get_db)):
    session = live_service.start_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.post("/{session_id}/next", response_model=LiveSession)
def next_question(session_id: int, db: Session = Depends(get_db)):
    session = live_service.next_question(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.post("/{session_id}/end", response_model=LiveSession)
def end_session(session_id: int, db: Session = Depends(get_db)):
    session = live_service.end_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.get("/{session_id}/status", response_model=LiveSession)
def get_session_status(session_id: int, db: Session = Depends(get_db)):
    session = live_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.get("/{session_id}/next_question", response_model=LiveQuestion | None)
def get_next_question(session_id: int, student_id: int, db: Session = Depends(get_db)):
    question = live_service.get_next_question_for_student(db, session_id, student_id)
    # If no question (finished), return None or specific message. Returning None is fine (200 OK null) or 204.
    # Frontend handles 'null' as finished/waiting.
    return question

@router.post("/{question_id}/answer", response_model=LiveAnswerResponse)
def submit_answer(question_id: int, payload: LiveAnswerRequest, db: Session = Depends(get_db)):
    try:
        response = live_service.submit_answer(
            db, 
            question_id, 
            payload.student_id, 
            payload.answer,
            payload.time_spent_seconds
        )
        return LiveAnswerResponse(
            status="submitted",
            is_correct=response.is_correct,
            # Hide correct answer from student
            correct_answer=None
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student ID or question ID")

@router.get("/class/{class_id}/active", response_model=LiveSession)
def get_active_session(class_id: int, db: Session = Depends(get_db)):
    session = live_service.get_active_session_for_class(db, class_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session for this class")
    return session

@router.get("/{session_id}/stats", response_model=LiveDashboardStats)
def get_session_stats(session_id: int, db: Session = Depends(get_db)):
    stats = live_service.get_session_stats(db, session_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stats unavailable")
    return stats


from app.schemas.live_events import LiveResponseRead, LiveResponseGrading

@router.get("/{session_id}/grading", response_model=list[LiveResponseRead])
def get_grading_tasks(session_id: int, db: Session = Depends(get_db)):
    # Get unscored responses (short answers pending review)
    return live_service.get_unscored_responses(db, session_id)

@router.post("/response/{response_id}/grade", response_model=LiveAnswerResponse)
def grade_student_response(response_id: int, payload: LiveResponseGrading, db: Session = Depends(get_db)):
    result = live_service.grade_response(db, response_id, payload.is_correct)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
        
    return LiveAnswerResponse(
        status="graded",
        is_correct=result.is_correct,
        correct_answer=None
    )


# Session History Endpoints
from app.schemas.live_events import LiveSessionSummary, LiveDetailedStats

@router.get("/class/{class_id}/history", response_model=list[LiveSessionSummary])
def get_session_history(class_id: int, db: Session = Depends(get_db)):
    """Get all sessions for a class with summary stats"""
    sessions = live_service.get_sessions_for_class(db, class_id)
    return [live_service.get_session_summary(db, s) for s in sessions]


@router.get("/{session_id}/detailed_stats", response_model=LiveDetailedStats)
def get_detailed_session_stats(session_id: int, db: Session = Depends(get_db)):
    """Get detailed per-student analytics for a session"""
    stats = live_service.get_detailed_session_stats(db, session_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return stats
