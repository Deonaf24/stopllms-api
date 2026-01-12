from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.school import MaterialCreate, MaterialRead, FileRead, FileCreate
from app.schemas.analytics import ConceptRead
from app.services import materials as materials_service
from app.services import assignments as assignments_service # Fallback for file schema
from app.services.storage import StorageError, get_storage_service
from app.services.rag import ingest_file

router = APIRouter(prefix="/school", tags=["school"])


@router.post("/classes/{class_id}/materials", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
def create_material(class_id: int, material_in: MaterialCreate, db: Session = Depends(get_db)):
    if material_in.class_id != class_id:
        raise HTTPException(status_code=400, detail="Class ID mismatch")
    material = materials_service.create_material(db, material_in)
    return materials_service.material_to_schema(material)


@router.get("/classes/{class_id}/materials", response_model=list[MaterialRead])
def list_materials(class_id: int, db: Session = Depends(get_db)):
    materials = materials_service.list_materials(db, class_id)
    return [materials_service.material_to_schema(m) for m in materials]


@router.post("/materials/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_material_file(
    material_id: int = Form(...),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    material = materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    storage = get_storage_service()
    try:
        # We can reuse assignment_id param for organization or add specific material path logic
        # For now, just using "materials/{material_id}" if storage supports, or just base
        # Storage service signature is save_upload(upload, assignment_id)
        # We might need to adjust storage service to accept arbitrary prefix or just overload assignment_id
        # Let's pass assignment_id=0 or similar if it's just for folder structure, or 
        # modify storage service.
        # Check storage service.
        stored = await storage.save_upload(upload=upload, assignment_id=f"material_{material_id}")
    except StorageError as exc:
        raise HTTPException(status_code=500, detail="Unable to persist uploaded file") from exc

    file_in = FileCreate(
        filename=upload.filename or "upload",
        storage_path=stored.path,
        storage_url=stored.url,
        mime_type=stored.mime_type,
        size=stored.size,
        material_id=material_id,
    )
    file = materials_service.create_material_file(db, file_in)
    
    # RAG ingestion? Materials might be useful for RAG too.
    # await ingest_file(upload, str(material.class_id) + "_materials") # logic TBD
    
    return assignments_service.file_to_schema(file)


@router.post("/materials/{material_id}/analyze", response_model=list[ConceptRead])
async def analyze_material(material_id: int, db: Session = Depends(get_db)):
    material = materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    concepts = await materials_service.analyze_material_content(db, material)
    return [ConceptRead.model_validate(c) for c in concepts]
