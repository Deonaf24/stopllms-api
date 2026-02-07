from __future__ import annotations

from datetime import datetime, date, time
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

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture_url: Optional[str] = None

class TeacherRead(TeacherBase, TimestampModel):
    id: int
    user_id: int
    name: str | None = None
    email: EmailStr | None = None
    profile_picture_url: str | None = None
    class_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)


class StudentBase(BaseModel):
    pass

class StudentCreate(BaseModel):
    user_id: int
    name: str
    email: EmailStr

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture_url: Optional[str] = None

class StudentRead(StudentBase, TimestampModel):
    id: int
    user_id: int
    name: str | None = None
    email: EmailStr | None = None
    profile_picture_url: str | None = None
    google_id: str | None = None
    class_ids: List[int] = Field(default_factory=list)


class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    teacher_id: Optional[int] = None
    join_code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class LectureBase(BaseModel):
    day_of_week: int
    start_time: time
    duration_minutes: int

class LectureCreate(LectureBase):
    pass

class LectureRead(LectureBase):
    id: int
    class_id: int
    start_time: time
    
    model_config = ConfigDict(from_attributes=True)



class ClassCreate(ClassBase):
    lectures: List[LectureCreate] = Field(default_factory=list)


class ClassRead(ClassBase, TimestampModel):
    id: int
    student_ids: List[int] = Field(default_factory=list)
    assignment_ids: List[int] = Field(default_factory=list)
    material_ids: List[int] = Field(default_factory=list)
    lectures: List[LectureRead] = Field(default_factory=list)
    material_ids: List[int] = Field(default_factory=list)
    lectures: List[LectureRead] = Field(default_factory=list)
    join_code: str
    
    google_id: str | None = None
    is_google_synced: bool = False


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



class StudentAssignmentInfo(BaseModel):
    student_id: int
    status: str | None = None
    grade: float | None = None
    google_submission_id: str | None = None

class AssignmentRead(AssignmentBase, TimestampModel):
    id: int
    file_ids: List[int] = Field(default_factory=list)
    google_id: str | None = None
    google_link: str | None = None
    submission: Optional[StudentAssignmentInfo] = None # For the requesting student
    all_submissions: List[StudentAssignmentInfo] = Field(default_factory=list) # For teachers (all students)


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
