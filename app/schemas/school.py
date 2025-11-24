from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherBase(BaseModel):
    pass

class TeacherCreate(BaseModel):
    user_id: int
    name: str
    email: EmailStr

class TeacherRead(TeacherBase, TimestampModel):
    id: int
    user_id: int
    class_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)


class StudentBase(BaseModel):
    pass

class StudentCreate(BaseModel):
    user_id: int
    name: str # MUST BE ADDED
    email: EmailStr # MUST BE ADDED

class StudentRead(StudentBase, TimestampModel):
    id: int
    user_id: int
    class_ids: List[int] = Field(default_factory=list)


class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    teacher_id: Optional[int] = None
    join_code: Optional[str] = None



class ClassCreate(ClassBase):
    pass


class ClassRead(ClassBase, TimestampModel):
    id: int
    student_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)
    join_code: str


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
    storage_path: str = Field(alias="path")
    assignment_id: int
    mime_type: str | None = None
    size: int = 0

    model_config = ConfigDict(populate_by_name=True)


class FileCreate(FileBase):
    pass


class FileRead(FileBase, TimestampModel):
    id: int

class JoinClassRequest(BaseModel):
    join_code: str
    student_id: int
