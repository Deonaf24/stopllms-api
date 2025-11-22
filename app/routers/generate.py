from fastapi import APIRouter, Depends
from app.core.deps import get_current_active_user
from app.schemas.prompts import PromptRequest
from app.services.prompts import build_prompt, retrieve_context
from app.services.llm import ollama_generate
from app.RAG.rag_db import get_db

router = APIRouter()

@router.post("/generate")
def generate(req: PromptRequest, current_user = Depends(get_current_active_user)):
    ctx = retrieve_context(get_db(), req.user_message)
    prompt = build_prompt(req, ctx)
    raw = ollama_generate(prompt)
    return {"answer": raw}