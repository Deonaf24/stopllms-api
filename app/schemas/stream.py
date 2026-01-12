from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class AnnouncementBase(BaseModel):
    title: str
    content: str
    class_id: int

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementRead(AnnouncementBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PollOptionBase(BaseModel):
    text: str

class PollOptionCreate(PollOptionBase):
    pass

class PollOptionRead(PollOptionBase):
    id: int
    poll_id: int
    # We might want to include vote count here for read
    vote_count: int = 0

    class Config:
        from_attributes = True

class PollBase(BaseModel):
    title: str
    description: Optional[str] = None
    question: str
    class_id: int

class PollCreate(PollBase):
    options: List[str] # List of option texts

class PollRead(PollBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    options: List[PollOptionRead]
    user_voted_option_id: Optional[int] = None # For the current user context

    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    poll_id: int
    option_id: int
    student_id: int
