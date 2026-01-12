from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.school import ClassCreate, ClassRead, JoinClassRequest
from app.services import classes as classes_service
from app.services import users as users_service

router = APIRouter(prefix="/school", tags=["school"])


@router.post("/classes", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    class_obj = classes_service.create_class(db, class_in)
    return classes_service.class_to_schema(class_obj)


@router.get("/classes", response_model=list[ClassRead])
def list_classes(db: Session = Depends(get_db)):
    classes = classes_service.list_classes(db)
    return [classes_service.class_to_schema(class_obj) for class_obj in classes]


@router.get("/classes/{class_id}", response_model=ClassRead)
def get_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = classes_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return classes_service.class_to_schema(class_obj)


@router.post(
    "/classes/{class_id}/students/{student_id}",
    response_model=ClassRead,
    status_code=status.HTTP_200_OK,
)
def enroll_student(class_id: int, student_id: int, db: Session = Depends(get_db)):
    class_obj = classes_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    student = users_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    updated_class = classes_service.enroll_student(db, class_obj, student)
    return classes_service.class_to_schema(updated_class)


@router.post("/classes/join", response_model=ClassRead)
def join_class_by_code(
    payload: JoinClassRequest,
    db: Session = Depends(get_db)
):
    class_obj = classes_service.get_class_by_join_code(db, payload.join_code)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid join code")

    student = users_service.get_student(db, payload.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    updated = classes_service.enroll_student(db, class_obj, student)
    return classes_service.class_to_schema(updated)


@router.get("/classes/{class_id}/concepts", response_model=list[dict])
def get_class_concepts(class_id: int, db: Session = Depends(get_db)):
    class_obj = classes_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    # Simple aggregation of unique concepts through assignments
    unique_concepts = {}
    for assignment in class_obj.assignments:
        for concept in assignment.concepts:
            if concept.id not in unique_concepts:
                unique_concepts[concept.id] = {
                    "id": concept.id,
                    "name": concept.name,
                    "description": concept.description
                }
    
    return list(unique_concepts.values())


from app.schemas.live_events import LiveQueryRequest, LiveQueryResponse
from app.services.live_events import generate_live_event_prompt

@router.post("/classes/{class_id}/live/generate", response_model=LiveQueryResponse)
async def generate_live_questions(
    class_id: int,
    request: LiveQueryRequest,
    db: Session = Depends(get_db)
):
    class_obj = classes_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        
    return await generate_live_event_prompt(db, class_id, request)
