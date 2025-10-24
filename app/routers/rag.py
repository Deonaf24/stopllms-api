from fastapi import APIRouter, Depends, FastAPI, File, UploadFile
from app.core.deps import get_current_active_user
from app.services.prompts import build_prompt, clean_quoted_output
from app.services.llm import ollama_generate
from app.services.rag import ingest_file
from typing import Annotated

router = APIRouter()

@router.post("/upload")
async def create_upload_file(file: UploadFile, current_user = Depends(get_current_active_user)):
    added = await ingest_file(file)
    return {"filename": file.filename}