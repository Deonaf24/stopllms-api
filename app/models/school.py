from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class_students = Table(
    "class_students",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class User(TimestampMixin, Base):
    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Authentication Fields (Unique and required for login)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # SECURITY FIELD: Stores the hashed password
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # State/Permissions
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship for Teacher
    teacher_link: Mapped[Teacher] = relationship(
        "Teacher", 
        back_populates="user_account",
        uselist=False,
        cascade="all, delete",
    )

    # Relationship for Student
    student_link: Mapped[Student] = relationship(
        "Student", 
        back_populates="user_account",
        uselist=False,
        cascade="all, delete",
    )

    @property
    def is_teacher(self) -> bool:
        # Falls back gently to no-profile
        try:
            return self.teacher_link is not None
        except:
            return False

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    user_account: Mapped[User] = relationship("User", back_populates="teacher_link")

    classes: Mapped[list[Class]] = relationship("Class", back_populates="teacher")
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="teacher"
    )

    def __repr__(self) -> str:
        return f"<Teacher id={self.id} email={self.email!r}>"


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    user_account: Mapped[User] = relationship("User", back_populates="student_link")

    classes: Mapped[list[Class]] = relationship(
        secondary=class_students, back_populates="students"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} email={self.email!r}>"


class Class(TimestampMixin, Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    join_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)

    teacher: Mapped[Teacher | None] = relationship("Teacher", back_populates="classes")
    students: Mapped[list[Student]] = relationship(
        secondary=class_students, back_populates="classes"
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="class_", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Class id={self.id} name={self.name!r}>"


class Assignment(TimestampMixin, Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )

    class_: Mapped[Class] = relationship("Class", back_populates="assignments")
    teacher: Mapped[Teacher | None] = relationship("Teacher", back_populates="assignments")
    files: Mapped[list[File]] = relationship(
        "File", back_populates="assignment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Assignment id={self.id} title={self.title!r}>"


class File(TimestampMixin, Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )

    assignment: Mapped[Assignment] = relationship("Assignment", back_populates="files")

    def __repr__(self) -> str:
        return f"<File id={self.id} filename={self.filename!r}>"


class ChatLog(TimestampMixin, Base):
    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)

    student: Mapped[User] = relationship("User")
    assignment: Mapped[Assignment] = relationship("Assignment")

    def __repr__(self) -> str:
        return f"<ChatLog id={self.id} student={self.student_id}>"
