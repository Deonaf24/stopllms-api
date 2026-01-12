from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.analytics import (
    AssignmentStructureReview,
    AssignmentStructureReviewRead,
    UnderstandingScoreRead,
)
from app.schemas.school import AssignmentCreate, AssignmentRead, AssignmentUpdate, FileCreate, FileRead
from app.services import assignments as assignments_service
from app.services.analysis import (
    AssignmentAnalysisError,
    analyze_assignment_structure,
    apply_assignment_structure,
    score_assignment_understanding,
)
from app.services.rag import ingest_file
from app.services.storage import StorageError, get_storage_service

router = APIRouter(prefix="/school", tags=["school"])


@router.post(
    "/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED
)
def create_assignment(assignment_in: AssignmentCreate, db: Session = Depends(get_db)):
    assignment = assignments_service.create_assignment(db, assignment_in)
    return assignments_service.assignment_to_schema(assignment)


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    assignments = assignments_service.list_assignments(db)
    return [assignments_service.assignment_to_schema(assignment) for assignment in assignments]


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignments_service.assignment_to_schema(assignment)


@router.put("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    assignment_in: AssignmentUpdate,
    db: Session = Depends(get_db),
):
    assignment = assignments_service.update_assignment(db, assignment_id, assignment_in)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignments_service.assignment_to_schema(assignment)


@router.delete("/assignments/{assignment_id}", response_model=AssignmentRead)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = assignments_service.delete_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignments_service.assignment_to_schema(assignment)


@router.delete("/assignments", response_model=list[AssignmentRead])
def delete_assignments(db: Session = Depends(get_db)):
    assignments = assignments_service.list_assignments(db)

    deleted_items = []

    for assignment in assignments:
        # Convert model to schema BEFORE deletion
        schema_copy = assignments_service.assignment_to_schema(assignment)

        db.delete(assignment)
        deleted_items.append(schema_copy)

    db.commit()

    return deleted_items


@router.post(
    "/assignments/{assignment_id}/analyze",
    response_model=AssignmentStructureReviewRead,
)
async def analyze_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    try:
        print(f"DEBUG: STARTING ANALYSIS for Assignment {assignment_id}")
        return await analyze_assignment_structure(db, assignment)
    except AssignmentAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put(
    "/assignments/{assignment_id}/structure",
    response_model=AssignmentStructureReviewRead,
)
def update_assignment_structure(
    assignment_id: int,
    payload: AssignmentStructureReview,
    db: Session = Depends(get_db),
):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    if payload.assignment_id != assignment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment ID mismatch")
    return apply_assignment_structure(db, assignment, payload)


@router.get(
    "/assignments/{assignment_id}/structure",
    response_model=AssignmentStructureReviewRead,
)
def get_assignment_structure(assignment_id: int, db: Session = Depends(get_db)):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    
    # Construct response from existing relationships
    # This logic mimics the "no-change" return of analyze_assignment_structure
    
    return AssignmentStructureReviewRead(
        assignment_id=assignment.id,
        concepts=[
            {"id": c.id, "name": c.name, "description": c.description} 
            for c in assignment.concepts
        ],
        questions=[
            {
                "id": q.id, 
                "prompt": q.prompt, 
                "position": q.position,
                "concept_ids": [c.id for c in q.concepts]
            }
            for q in assignment.questions
        ],
        question_concepts=[
            {"question_id": q.id, "concept_id": c.id}
            for q in assignment.questions
            for c in q.concepts
        ],
        assignment_concepts=[
            {"concept_id": c.id} for c in assignment.concepts
        ],
        structure_approved=assignment.structure_approved,
    )


@router.post(
    "/assignments/{assignment_id}/score",
    response_model=list[UnderstandingScoreRead],
)
async def score_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    try:
        scores = await score_assignment_understanding(db, assignment)
    except AssignmentAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [
        UnderstandingScoreRead(
            id=score.id,
            student_id=score.student_id,
            assignment_id=score.assignment_id,
            question_id=score.question_id,
            concept_id=score.concept_id,
            score=score.score,
            confidence=score.confidence,
            source=score.source,
            created_at=score.created_at,
            updated_at=score.updated_at,
        )
        for score in scores
    ]


# ============================================================
# FILES (metadata only — not file upload)
# ============================================================

@router.post("/files", response_model=FileRead, status_code=status.HTTP_201_CREATED)
def create_file(file_in: FileCreate, db: Session = Depends(get_db)):
    assignment = assignments_service.get_assignment(db, file_in.assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    file = assignments_service.create_file(db, file_in)
    return assignments_service.file_to_schema(file)


@router.get("/files", response_model=list[FileRead])
def list_files(db: Session = Depends(get_db)):
    files = assignments_service.list_files(db)
    return [assignments_service.file_to_schema(file) for file in files]


@router.get("/files/{file_id}", response_model=FileRead)
def get_file(file_id: int, db: Session = Depends(get_db)):
    file = assignments_service.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return assignments_service.file_to_schema(file)


@router.post(
    "/files/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    assignment_id: int = Form(...),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    assignment = assignments_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    storage = get_storage_service()
    try:
        stored = await storage.save_upload(upload=upload, assignment_id=assignment_id)
    except StorageError as exc:  # pragma: no cover - passthrough
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist uploaded file",
        ) from exc

    file_in = FileCreate(
        filename=upload.filename or "upload",
        storage_path=stored.path,
        storage_url=stored.url,
        mime_type=stored.mime_type,
        size=stored.size,
        assignment_id=assignment_id,
    )
    file = assignments_service.create_file(db, file_in)
    await ingest_file(upload, str(assignment.id))
    await upload.close()
    return assignments_service.file_to_schema(file)


@router.get("/files/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    file = assignments_service.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    storage = get_storage_service()

    # CASE 1 — PREFERRING PUBLIC URL if available (S3 or static URL)
    if file.url:
        return RedirectResponse(url=file.url)

    # CASE 2 — LOCAL FS or PRIVATE STORAGE (load bytes manually)
    try:
        data = await storage.open_file(file.path)
    except StorageError:
        raise HTTPException(status_code=404, detail="Stored file could not be accessed")

    return StreamingResponse(
        iter([data]),
        media_type=file.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{file.filename}"',
            "Content-Length": str(len(data)),
        },
    )
