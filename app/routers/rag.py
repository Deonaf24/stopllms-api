from fastapi import APIRouter, Depends, UploadFile

from app.core.deps import get_current_active_user
from app.services.rag import ingest_file, clear_databased

router = APIRouter()


@router.post("/upload")
async def create_upload_file(
    file: UploadFile,
    assignment_id: str,
    current_user=Depends(get_current_active_user),
):
    await ingest_file(file, assignment_id)
    return {"filename": file.filename}


@router.delete("/clear")
async def clear_database(
    assignment_id: str,
    current_user=Depends(get_current_active_user),
):
    return clear_databased(assignment_id)


@router.delete("/delete")
async def delete_file():
    ...
