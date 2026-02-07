from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: int
    order: int = 0

class ChapterCreate(ChapterBase):
    pass

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    
    # Optional: Allow updating links directly? Usually handled via separate endpoints or lists of IDs.
    # For now, keep it simple.

class ChapterRead(ChapterBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Included IDs for relationships
    concept_ids: List[int] = []
    assignment_ids: List[int] = []
    material_ids: List[int] = []

    class Config:
        from_attributes = True

class ChapterLinkUpdate(BaseModel):
    ids: List[int]
