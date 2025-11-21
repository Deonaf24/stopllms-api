from fastapi import APIRouter, Depends, UploadFile

from app.core.deps import get_current_active_user
from app.services.rag import ingest_file

router = APIRouter()


@router.post("/upload")
async def create_upload_file(
    file: UploadFile,
    current_user=Depends(get_current_active_user),
):
    added = await ingest_file(file)
    return {"filename": file.filename, "chunks_added": added}
