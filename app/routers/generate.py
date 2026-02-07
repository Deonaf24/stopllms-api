from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db as get_sql_db
from app.core.deps import get_current_active_user
from app.models.school import ChatLog, Assignment
from app.schemas.prompts import PromptRequest
from app.services.ai.prompts import build_prompt, retrieve_context
from app.services.ai.llm import generate_text
from app.services.ai.rag.rag_db import get_db

router = APIRouter()


@router.post("/generate")
def generate(
    req: PromptRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_sql_db),
):
    # Fetch Student Learning Context for all prompt types
    from app.services.ai.context import get_student_learning_summary
    student_summary = get_student_learning_summary(db, current_user.id)

    # Special handling for Lesson Planner (no assignment ID)
    if req.assignment_id == "planning":
        profile_context = student_summary # Default fallback
        if req.class_id:
             from app.services.ai.context import get_class_learning_summary
             class_summary = get_class_learning_summary(db, int(req.class_id))
             if class_summary:
                 profile_context = class_summary
        
        prompt = build_prompt(req, [], prompt_type="lesson_planner", student_profile=profile_context)
        raw = generate_text(prompt)
        return {"answer": raw}

    # Special handling for Study Planner
    if req.assignment_id == "study-planning":
        prompt = build_prompt(req, [], prompt_type="study_planner", student_profile=student_summary)
        raw = generate_text(prompt)
        return {"answer": raw}

    # Log the interaction for analytics
    chat_log = ChatLog(
        student_id=current_user.id,
        assignment_id=int(req.assignment_id),
        question=req.user_message,
    )
    db.add(chat_log)
    db.commit()

    ctx = retrieve_context(get_db(str(req.assignment_id)), req.user_message)
    
    tutor_subject = "math"
    if req.assignment_id.isdigit():
        assign = db.get(Assignment, int(req.assignment_id))
        if assign and assign.class_:
             tutor_subject = assign.class_.name

    prompt = build_prompt(req, ctx, tutor_subject=tutor_subject, student_profile=student_summary)
    raw = generate_text(prompt)
    return {"answer": raw}
