from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherBase(BaseModel):
    name: str
    email: str


class TeacherCreate(TeacherBase):
    pass


class TeacherRead(TeacherBase, TimestampModel):
    id: int
    class_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)


class StudentBase(BaseModel):
    name: str
    email: str


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase, TimestampModel):
    id: int
    class_ids: List[int] = Field(default_factory=list)


class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    teacher_id: Optional[int] = None


class ClassCreate(ClassBase):
    pass


class ClassRead(ClassBase, TimestampModel):
    id: int
    student_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    class_id: int
    teacher_id: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentRead(AssignmentBase, TimestampModel):
    id: int
    file_ids: List[int] = Field(default_factory=list)


class FileBase(BaseModel):
    filename: str
    path: str
    assignment_id: int


class FileCreate(FileBase):
    pass


class FileRead(FileBase, TimestampModel):
    id: int
