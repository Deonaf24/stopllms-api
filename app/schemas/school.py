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
    name: str | None = None
    email: EmailStr | None = None
    class_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)


class StudentBase(BaseModel):
    pass

class StudentCreate(BaseModel):
    user_id: int
    name: str
    email: EmailStr

class StudentRead(StudentBase, TimestampModel):
    id: int
    user_id: int
    name: str | None = None
    email: EmailStr | None = None
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
    material_ids: List[int] = Field(default_factory=list)
    join_code: str


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    class_id: int
    teacher_id: Optional[int] = None
    level: int = 1


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    level: Optional[int] = None
    file_ids: Optional[List[int]] = None # Allow updating file list conceptually if needed, or just standard metadata



class AssignmentRead(AssignmentBase, TimestampModel):
    id: int
    file_ids: List[int] = Field(default_factory=list)


class MaterialBase(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: int
    teacher_id: int


class MaterialCreate(MaterialBase):
    concept_ids: List[int] = Field(default_factory=list)


class MaterialRead(MaterialBase, TimestampModel):
    id: int
    file_ids: List[int] = Field(default_factory=list)
    concept_ids: List[int] = Field(default_factory=list)


class FileBase(BaseModel):
    filename: str
    storage_path: str = Field(alias="path")
    storage_url: str | None = Field(default=None, alias="url")
    assignment_id: Optional[int] = None
    material_id: Optional[int] = None
    announcement_id: Optional[int] = None
    poll_id: Optional[int] = None
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
