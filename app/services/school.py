from __future__ import annotations
import string
import random

from sqlalchemy.orm import Session

from app.models.school import Assignment, Class, File, Student, Teacher
from app.schemas.school import (
    AssignmentCreate,
    AssignmentRead,
    ClassCreate,
    ClassRead,
    FileCreate,
    FileRead,
    StudentCreate,
    StudentRead,
    TeacherCreate,
    TeacherRead,
)

def generate_join_code(k=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))


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


def assignment_to_schema(assignment: Assignment) -> AssignmentRead:
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
    return FileRead(
        id=file.id,
        filename=file.filename,
        storage_path=file.path,
        assignment_id=file.assignment_id,
        created_at=file.created_at,
        updated_at=file.updated_at,
    )
