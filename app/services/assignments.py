from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.school import Assignment, AssignmentQuestion, Concept, File

if TYPE_CHECKING:
    from app.schemas.school import AssignmentCreate, AssignmentRead, FileCreate, FileRead

__all__ = [
    "create_assignment",
    "list_assignments",
    "get_assignment",
    "delete_assignment",
    "create_file",
    "list_files",
    "get_file",
    "list_assignment_questions",
    "list_assignment_concepts",
    "assignment_to_schema",
    "file_to_schema",
]


def create_assignment(db: Session, assignment_in: AssignmentCreate) -> Assignment:
    assignment = Assignment(**assignment_in.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(db: Session) -> list[Assignment]:
    return db.query(Assignment).all()


def get_assignment(db: Session, assignment_id: int) -> Assignment | None:
    return db.get(Assignment, assignment_id)


def delete_assignment(db: Session, assignment_id: int) -> Assignment | None:
    ass = db.get(Assignment, assignment_id)
    if not ass:
        return None

    db.delete(ass)
    db.commit()   # VERY IMPORTANT
    return ass    # return the deleted object



def create_file(db: Session, file_in: FileCreate) -> File:
    file = File(**file_in.model_dump(by_alias=True))
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


def list_files(db: Session) -> list[File]:
    return db.query(File).all()


def get_file(db: Session, file_id: int) -> File | None:
    return db.get(File, file_id)


def list_assignment_questions(db: Session, assignment_id: int) -> list[AssignmentQuestion]:
    return (
        db.query(AssignmentQuestion)
        .filter(AssignmentQuestion.assignment_id == assignment_id)
        .order_by(AssignmentQuestion.position.asc().nulls_last(), AssignmentQuestion.id.asc())
        .all()
    )


def list_assignment_concepts(db: Session, assignment_id: int) -> list[Concept]:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        return []
    return list(assignment.concepts)


def assignment_to_schema(assignment: Assignment) -> AssignmentRead:
    from app.schemas.school import AssignmentRead

    return AssignmentRead(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        due_at=assignment.due_at,
        class_id=assignment.class_id,
        teacher_id=assignment.teacher_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        file_ids=[file.id for file in assignment.files],
    )


def file_to_schema(file: File) -> FileRead:
    from app.schemas.school import FileRead

    return FileRead(
        id=file.id,
        filename=file.filename,
        storage_path=file.path,
        storage_url=file.url,
        mime_type=file.mime_type,
        size=file.size,
        assignment_id=file.assignment_id,
        created_at=file.created_at,
        updated_at=file.updated_at,
    )
