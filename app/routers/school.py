from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.schemas.school import (
    AssignmentCreate,
    AssignmentRead,
    ClassCreate,
    ClassRead,
    FileCreate,
    FileRead,
    JoinClassRequest,
    StudentCreate,
    StudentRead,
    TeacherCreate,
    TeacherRead,
)
from app.services import school as school_service

router = APIRouter(prefix="/school", tags=["school"])


@router.post("/teachers", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher_in: TeacherCreate, db: Session = Depends(get_db)):
    teacher = school_service.create_teacher(db, teacher_in)
    return school_service.teacher_to_schema(teacher)


@router.get("/teachers", response_model=list[TeacherRead])
def list_teachers(db: Session = Depends(get_db)):
    teachers = school_service.list_teachers(db)
    return [school_service.teacher_to_schema(teacher) for teacher in teachers]


@router.get("/teachers/{teacher_id}", response_model=TeacherRead)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = school_service.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return school_service.teacher_to_schema(teacher)


@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    student = school_service.create_student(db, student_in)
    return school_service.student_to_schema(student)


@router.get("/students", response_model=list[StudentRead])
def list_students(db: Session = Depends(get_db)):
    students = school_service.list_students(db)
    return [school_service.student_to_schema(student) for student in students]


@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = school_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return school_service.student_to_schema(student)


@router.post("/classes", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    class_obj = school_service.create_class(db, class_in)
    return school_service.class_to_schema(class_obj)


@router.get("/classes", response_model=list[ClassRead])
def list_classes(db: Session = Depends(get_db)):
    classes = school_service.list_classes(db)
    return [school_service.class_to_schema(class_obj) for class_obj in classes]


@router.get("/classes/{class_id}", response_model=ClassRead)
def get_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = school_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return school_service.class_to_schema(class_obj)


@router.post(
    "/classes/{class_id}/students/{student_id}",
    response_model=ClassRead,
    status_code=status.HTTP_200_OK,
)
def enroll_student(class_id: int, student_id: int, db: Session = Depends(get_db)):
    class_obj = school_service.get_class(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    student = school_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    updated_class = school_service.enroll_student(db, class_obj, student)
    return school_service.class_to_schema(updated_class)

@router.post("/classes/join", response_model=ClassRead)
def join_class_by_code(
    payload: JoinClassRequest,
    db: Session = Depends(get_db)
):
    class_obj = school_service.get_class_by_join_code(db, payload.join_code)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid join code")

    student = school_service.get_student(db, payload.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    updated = school_service.enroll_student(db, class_obj, student)
    return school_service.class_to_schema(updated)





@router.post(
    "/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED
)
def create_assignment(assignment_in: AssignmentCreate, db: Session = Depends(get_db)):
    assignment = school_service.create_assignment(db, assignment_in)
    return school_service.assignment_to_schema(assignment)


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    assignments = school_service.list_assignments(db)
    return [school_service.assignment_to_schema(assignment) for assignment in assignments]


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = school_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return school_service.assignment_to_schema(assignment)

# ============================================================
# FILES (metadata only — not file upload)
# ============================================================

@router.post("/files", response_model=FileRead, status_code=status.HTTP_201_CREATED)
def create_file(file_in: FileCreate, db: Session = Depends(get_db)):
    assignment = school_service.get_assignment(db, file_in.assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    file = school_service.create_file(db, file_in)
    return school_service.file_to_schema(file)


@router.get("/files", response_model=list[FileRead])
def list_files(db: Session = Depends(get_db)):
    files = school_service.list_files(db)
    return [school_service.file_to_schema(file) for file in files]


@router.get("/files/{file_id}", response_model=FileRead)
def get_file(file_id: int, db: Session = Depends(get_db)):
    file = school_service.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return school_service.file_to_schema(file)


@router.post(
    "/files/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    assignment_id: int = Form(...),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    assignment = school_service.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    storage_dir = Path(settings.FILE_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    original_name = upload.filename or "upload"
    safe_name = Path(original_name).name
    storage_name = f"{uuid4().hex}_{safe_name}"
    destination = storage_dir / storage_name

    total_size = 0

    with destination.open("wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
            total_size += len(chunk)

    await upload.close()

    file_in = FileCreate(
        filename=safe_name,
        storage_path=str(destination),
        mime_type=upload.content_type,
        size=total_size,
        assignment_id=assignment_id,
    )
    file = school_service.create_file(db, file_in)
    return school_service.file_to_schema(file)
