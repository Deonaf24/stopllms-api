from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user
from app.services import assignments as assignments_service
from app.services.rag import ingest_file, clear_database

router = APIRouter()


@router.post("/upload")
async def create_upload_file(
    file: UploadFile,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await ingest_file(file, str(assignment_id))
    return {"filename": file.filename}


@router.delete("/clear")
async def clear_database(
    assignment_id: str,
    current_user=Depends(get_current_active_user),
):
    return clear_database(assignment_id)


@router.delete("/delete")
async def delete_file():
    ...
