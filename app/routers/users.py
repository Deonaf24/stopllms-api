from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.school import (
    StudentCreate,
    StudentRead,
    StudentUpdate,
    TeacherCreate,
    TeacherRead,
    TeacherUpdate,
)
from app.services.school import users as users_service

router = APIRouter(prefix="/school", tags=["school"])


@router.post("/teachers", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher_in: TeacherCreate, db: Session = Depends(get_db)):
    teacher = users_service.create_teacher(db, teacher_in)
    return users_service.teacher_to_schema(teacher)


@router.get("/teachers", response_model=list[TeacherRead])
def list_teachers(db: Session = Depends(get_db)):
    teachers = users_service.list_teachers(db)
    return [users_service.teacher_to_schema(teacher) for teacher in teachers]


@router.get("/teachers/{teacher_id}", response_model=TeacherRead)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = users_service.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return users_service.teacher_to_schema(teacher)


@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    student = users_service.create_student(db, student_in)
    return users_service.student_to_schema(student)


@router.get("/students", response_model=list[StudentRead])
def list_students(db: Session = Depends(get_db)):
    students = users_service.list_students(db)
    return [users_service.student_to_schema(student) for student in students]


@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = users_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return users_service.student_to_schema(student)


@router.put("/teachers/{teacher_id}", response_model=TeacherRead)
def update_teacher(teacher_id: int, teacher_in: TeacherUpdate, db: Session = Depends(get_db)):
    teacher = users_service.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    
    teacher = users_service.update_teacher(db, teacher, teacher_in)
    return users_service.teacher_to_schema(teacher)


@router.put("/students/{student_id}", response_model=StudentRead)
def update_student(student_id: int, student_in: StudentUpdate, db: Session = Depends(get_db)):
    student = users_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    student = users_service.update_student(db, student, student_in)
    return users_service.student_to_schema(student)


@router.post("/users/avatar", status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile,  # Assuming this import from fastapi is available or I need to add it
):
    from app.services.storage import get_storage_service, StorageError # Local import to avoid circular dependency if any, or just convenience

    storage = get_storage_service()
    try:
        stored = await storage.save_upload(upload=file, folder="avatars")
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save avatar",
        ) from exc
        
    return {"url": stored.url}
