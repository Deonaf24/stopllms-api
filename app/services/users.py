from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.school import Student, Teacher
from app.schemas.school import (
    StudentCreate,
    StudentRead,
    TeacherCreate,
    TeacherRead,
)

__all__ = [
    "create_teacher",
    "list_teachers",
    "get_teacher",
    "create_student",
    "list_students",
    "get_student",
    "teacher_to_schema",
    "student_to_schema",
]


def create_teacher(db: Session, teacher_in: TeacherCreate) -> Teacher:
    teacher = Teacher(**teacher_in.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def list_teachers(db: Session) -> list[Teacher]:
    return db.query(Teacher).all()


def get_teacher(db: Session, teacher_id: int) -> Teacher | None:
    return db.get(Teacher, teacher_id)


def create_student(db: Session, student_in: StudentCreate) -> Student:
    student = Student(**student_in.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def list_students(db: Session) -> list[Student]:
    return db.query(Student).all()


def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def teacher_to_schema(teacher: Teacher) -> TeacherRead:
    return TeacherRead(
        id=teacher.id,
        name=teacher.name,
        email=teacher.email,
        user_id=teacher.user_id,
        created_at=teacher.created_at,
        updated_at=teacher.updated_at,
        class_ids=[class_.id for class_ in teacher.classes],
        assignment_ids=[assignment.id for assignment in teacher.assignments],
    )


def student_to_schema(student: Student) -> StudentRead:
    return StudentRead(
        id=student.id,
        name=student.name,
        email=student.email,
        user_id=student.user_id,
        created_at=student.created_at,
        updated_at=student.updated_at,
        class_ids=[class_.id for class_ in student.classes],
    )
