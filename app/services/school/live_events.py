from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.school import Class, Concept, Material, Assignment, File, LiveSession, LiveQuestion, LiveResponse
from app.schemas.live_events import LiveQueryRequest, LiveQueryResponse, LiveSession as LiveSessionSchema
from app.services.ai.content import extract_content_from_files
from app.services.ai.prompts import build_live_event_generation_prompt
from app.services.ai.llm import generate_text

import json
import logging

logger = logging.getLogger(__name__)

async def generate_live_event_prompt(db: Session, class_id: int, request: LiveQueryRequest) -> LiveQueryResponse:
    # 1. Get Concepts
    concepts = db.query(Concept).filter(Concept.id.in_(request.concept_ids)).all()
    concept_names = [c.name for c in concepts]
    
    # 2. Find relevant Materials and Assignments in this class linked to these concepts
    # Retrieve materials that have AT LEAST one of the selected concept IDs
    materials = (
        db.query(Material)
        .filter(Material.class_id == class_id)
        .filter(Material.concepts.any(Concept.id.in_(request.concept_ids)))
        .all()
    )
    
    assignments = (
        db.query(Assignment)
        .filter(Assignment.class_id == class_id)
        .filter(Assignment.concepts.any(Concept.id.in_(request.concept_ids)))
        .all()
    )
    
    # 3. Collect Files
    all_files = []
    for m in materials:
        all_files.extend(m.files)
    for a in assignments:
        all_files.extend(a.files)
        
    # Remove duplicates if any (though unlikely with current model structure unless shared files existed)
    unique_files = {f.id: f for f in all_files}.values()
    
    # 4. Extract Content
    combined_text, file_payloads = await extract_content_from_files(list(unique_files))
    
    context_summary = f"Found {len(materials)} materials and {len(assignments)} assignments with {len(unique_files)} files."
    
    # 5. Build Prompt
    final_text_context = combined_text
    if not final_text_context and not file_payloads:
        final_text_context = "(No file content found. Questions will be based on concept names only.)"
        
    prompt = build_live_event_generation_prompt(concept_names, final_text_context, request.time_limit, request.question_type)
    
    # 6. Call LLM
    logger.info("Generating live event questions via LLM...")
    response_text = generate_text(prompt, files=file_payloads)
    
    # Clean up response (remove markdown code blocks if present)
    response_text = response_text.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(response_text)
        questions_data = data.get("questions", [])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {response_text}")
        # Fallback empty session or raise error? For now, empty list
        questions_data = []

    # 7. Create Session in DB
    session = LiveSession(
        class_id=class_id,
        status="active",
        current_question_index=0,
        concept_ids=request.concept_ids
    )
    db.add(session)
    db.flush()
    
    # 8. Create Questions
    db_questions = []
    for i, q_data in enumerate(questions_data):
        # Handle options serialization
        opts = q_data.get("options")
        
        # Determine type: use LLM provided type, or fallback to first requested type
        q_type = q_data.get("question_type")
        if not q_type or q_type not in ["multiple_choice", "true_false", "short_answer"]:
             q_type = request.question_type[0] if request.question_type else "multiple_choice"

        question = LiveQuestion(
            session_id=session.id,
            text=q_data.get("text", "Question text missing"),
            question_type=q_type, 
            options=opts, 
            correct_answer=str(q_data.get("correct_answer", "")),
            order=i
        )
        db.add(question)
        db_questions.append(question)
        
    db.commit()
    db.refresh(session)
    
    # 9. Return Response
    return LiveQueryResponse(
        session=LiveSessionSchema.model_validate(session),
        context_summary=context_summary
    )

def get_session(db: Session, session_id: int) -> LiveSession | None:
    return db.query(LiveSession).filter(LiveSession.id == session_id).first()

def start_session(db: Session, session_id: int) -> LiveSession | None:
    session = get_session(db, session_id)
    if not session:
        return None
    session.status = "active"
    session.current_question_index = 0
    db.commit()
    db.refresh(session)
    return session

def next_question(db: Session, session_id: int) -> LiveSession | None:
    session = get_session(db, session_id)
    if not session:
        return None
    
    # Check if there are more questions
    total_questions = len(session.questions)
    if session.current_question_index < total_questions - 1:
        session.current_question_index += 1
    else:
        # Loop or just stay at end? Let's just stay for now, or could set status to ended
        pass 
        
    db.commit()
    db.refresh(session)
    return session

def end_session(db: Session, session_id: int) -> LiveSession | None:
    session = get_session(db, session_id)
    if not session:
        return None
    session.status = "ended"
    # session.ended_at = func.now() # need import func or just datetime.now
    from datetime import datetime
    session.ended_at = datetime.now()
    db.commit()
    db.refresh(session)
    from app.services.analysis.analytics_processing import process_live_session_results
    process_live_session_results(db, session_id)
    return session

def submit_answer(db: Session, question_id: int, student_id: int, answer: str, time_spent_seconds: int) -> LiveResponse:
    # Get question to check correctness
    question = db.query(LiveQuestion).filter(LiveQuestion.id == question_id).first()
    if not question:
        raise ValueError("Question not found")
        
    # Check correctness
    # If short_answer, we DO NOT auto-grade. Leave as None.
    if question.question_type == "short_answer":
        is_correct = None
    else:
        # Simple direct match for now. For MC, answer is the option text.
        is_correct = (answer.strip().lower() == str(question.correct_answer).strip().lower())
    
    # Create Response
    response = LiveResponse(
        question_id=question_id,
        student_id=student_id,
        answer=answer,
        is_correct=is_correct,
        time_spent_seconds=time_spent_seconds
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Return response without revealing correctness
    # We construct the Pydantic model manually to control what's returned if needed, 
    # but the schema now allows None. 
    # The requirement is "answers shouldnt be revealed to students".
    # So we simply return is_correct=None in the API response, even if we calculated it for MC.
    return LiveResponse(
        id=response.id,
        question_id=question_id,
        student_id=student_id,
        answer=answer,
        is_correct=None, # HIDE RESULT
        time_spent_seconds=time_spent_seconds
    )

def get_next_question_for_student(db: Session, session_id: int, student_id: int) -> LiveQuestion | None:
    session = get_session(db, session_id)
    if not session or session.status != "active":
        return None
        
    # Get total questions
    questions = sorted(session.questions, key=lambda q: q.order)
    
    # Get student's answer count for this session's questions
    # Join LiveResponse on LiveQuestion where session_id matches
    answered_count = (
        db.query(LiveResponse)
        .join(LiveQuestion)
        .filter(LiveQuestion.session_id == session_id)
        .filter(LiveResponse.student_id == student_id)
        .count()
    )
    
    # If answered_count < total, return questions[answered_count]
    if answered_count < len(questions):
        return questions[answered_count]
        
    return None # Finished all questions

def get_active_session_for_class(db: Session, class_id: int) -> LiveSession | None:
    return (
        db.query(LiveSession)
        .filter(LiveSession.class_id == class_id)
        .filter(LiveSession.status == "active")
        .order_by(LiveSession.created_at.desc())
        .first()
    )

def get_session_stats(db: Session, session_id: int):
    session = get_session(db, session_id)
    if not session:
        return None
        
    stats_list = []
    
    # Calculate stats for EACH question
    for q in session.questions:
        responses = db.query(LiveResponse).filter(LiveResponse.question_id == q.id).all()
        
        distribution = {}
        if q.options:
            for opt in q.options:
                distribution[str(opt)] = 0
                
        for r in responses:
            ans = str(r.answer)
            distribution[ans] = distribution.get(ans, 0) + 1
            
        stats_list.append({
            "question_id": q.id,
            "total_responses": len(responses),
            "distribution": distribution
        })
        
    return {
        "session_id": session.id,
        "total_students": 0, 
        "questions": stats_list
    }

def get_unscored_responses(db: Session, session_id: int):
    # Fetch responses for this session where is_correct is explicitly None
    # We join LiveQuestion to ensure session matching
    responses = (
        db.query(LiveResponse, LiveQuestion.text)
        .join(LiveQuestion, LiveQuestion.id == LiveResponse.question_id)
        .filter(LiveQuestion.session_id == session_id)
        .filter(LiveResponse.is_correct == None)
        .all()
    )
    
    # Map to schema manually or use object
    results = []
    for r, q_text in responses:
        # r is LiveResponse object
        # We attach q_text for convenience
        r.question_text = q_text 
        results.append(r)
        
    return results

def grade_response(db: Session, response_id: int, is_correct: bool):
    response = db.query(LiveResponse).filter(LiveResponse.id == response_id).first()
    if not response:
        return None
        
    response.is_correct = is_correct
    db.commit()
    db.refresh(response)
    
    # Trigger analytics Update? 
    # Ideally yes, if we want this to update context, we might need to re-run processing or just rely on next batch.
    # The user "answers shouldnt automatically be graded".
    # But after manual grading, they ARE graded.
    # So we should probably allow re-processing if session is ended. 
    # For now, just saving is enough.
    
    return response


def get_sessions_for_class(db: Session, class_id: int) -> list[LiveSession]:
    """Get all sessions for a class, ordered by most recent first"""
    return (
        db.query(LiveSession)
        .filter(LiveSession.class_id == class_id)
        .order_by(LiveSession.created_at.desc())
        .all()
    )


def get_session_summary(db: Session, session: LiveSession) -> dict:
    """Build a summary dict for a session"""
    question_count = len(session.questions)
    
    # Count total responses across all questions
    response_count = (
        db.query(LiveResponse)
        .join(LiveQuestion)
        .filter(LiveQuestion.session_id == session.id)
        .count()
    )
    
    # Count unique participants
    participant_count = (
        db.query(LiveResponse.student_id)
        .join(LiveQuestion)
        .filter(LiveQuestion.session_id == session.id)
        .distinct()
        .count()
    )
    
    return {
        "id": session.id,
        "class_id": session.class_id,
        "status": session.status,
        "created_at": session.created_at,
        "ended_at": session.ended_at,
        "question_count": question_count,
        "response_count": response_count,
        "participant_count": participant_count
    }


def get_detailed_session_stats(db: Session, session_id: int) -> dict | None:
    """Get detailed per-student analytics for a session"""
    session = get_session(db, session_id)
    if not session:
        return None
    
    # Build question list
    questions = [
        {
            "id": q.id,
            "text": q.text,
            "question_type": q.question_type,
            "options": q.options,
            "order": q.order
        }
        for q in sorted(session.questions, key=lambda x: x.order)
    ]
    
    # Get all responses for this session, grouped by student
    all_responses = (
        db.query(LiveResponse, LiveQuestion)
        .join(LiveQuestion, LiveQuestion.id == LiveResponse.question_id)
        .filter(LiveQuestion.session_id == session_id)
        .all()
    )
    
    # Group by student
    student_data: dict[int, list] = {}
    for response, question in all_responses:
        if response.student_id not in student_data:
            student_data[response.student_id] = []
        student_data[response.student_id].append({
            "question_id": question.id,
            "question_text": question.text,
            "question_type": question.question_type,
            "answer": response.answer,
            "is_correct": response.is_correct,
            "time_spent_seconds": response.time_spent_seconds or 0
        })
    
    # Build student results
    student_results = []
    total_graded = 0
    total_correct = 0
    
    for student_id, responses in student_data.items():
        correct = sum(1 for r in responses if r["is_correct"] is True)
        answered = len(responses)
        graded = sum(1 for r in responses if r["is_correct"] is not None)
        
        total_graded += graded
        total_correct += correct
        
        student_results.append({
            "student_id": student_id,
            "total_correct": correct,
            "total_answered": answered,
            "responses": responses
        })
    
    # Overall accuracy
    overall_accuracy = (total_correct / total_graded * 100) if total_graded > 0 else 0.0
    
    return {
        "session_id": session.id,
        "class_id": session.class_id,
        "created_at": session.created_at,
        "ended_at": session.ended_at,
        "questions": questions,
        "student_results": student_results,
        "overall_accuracy": round(overall_accuracy, 1)
    }
