from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db as get_sql_db
from app.core.deps import get_current_active_user
from app.models.school import ChatLog
from app.schemas.prompts import PromptRequest
from app.services.prompts import build_prompt, retrieve_context
from app.services.llm import ollama_generate
from app.RAG.rag_db import get_db

router = APIRouter()


@router.post("/generate")
def generate(
    req: PromptRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_sql_db),
):
    # Log the interaction for analytics
    chat_log = ChatLog(
        student_id=current_user.id,
        assignment_id=int(req.assignment_id),
        question=req.user_message,
    )
    db.add(chat_log)
    db.commit()

    ctx = retrieve_context(get_db(req.assignment_id), req.user_message)
    prompt = build_prompt(req, ctx)
    raw = ollama_generate(prompt)
    return {"answer": raw}
