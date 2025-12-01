from __future__ import annotations

import random
import string

from sqlalchemy.orm import Session

from app.models.school import Class, Student
from app.schemas.school import ClassCreate, ClassRead

__all__ = [
    "generate_join_code",
    "create_class",
    "list_classes",
    "get_class",
    "get_class_by_join_code",
    "enroll_student",
    "class_to_schema",
]


def generate_join_code(k=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))


def create_class(db: Session, class_in: ClassCreate) -> Class:
    data = class_in.model_dump()

    if "join_code" not in data or not data["join_code"]:
        data["join_code"] = generate_join_code()

    class_obj = Class(**data)
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    return class_obj


def list_classes(db: Session) -> list[Class]:
    return db.query(Class).all()


def get_class(db: Session, class_id: int) -> Class | None:
    return db.get(Class, class_id)


def get_class_by_join_code(db: Session, code: str) -> Class | None:
    return db.query(Class).filter(Class.join_code == code).first()


def enroll_student(db: Session, class_obj: Class, student: Student) -> Class:
    if student not in class_obj.students:
        class_obj.students.append(student)
        db.add(class_obj)
        db.commit()
        db.refresh(class_obj)
    return class_obj


def class_to_schema(class_obj: Class) -> ClassRead:
    return ClassRead(
        id=class_obj.id,
        name=class_obj.name,
        description=class_obj.description,
        teacher_id=class_obj.teacher_id,
        join_code=class_obj.join_code,
        created_at=class_obj.created_at,
        updated_at=class_obj.updated_at,
        student_ids=[student.id for student in class_obj.students],
        assignment_ids=[assignment.id for assignment in class_obj.assignments],
    )
