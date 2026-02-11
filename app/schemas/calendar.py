from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CalendarEventBase(BaseModel):
    """Base schema for calendar events."""
    title: str
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    class_id: Optional[int] = None
    source: Optional[str] = None  # e.g., "study_plan", "manual"


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a calendar event."""
    pass


class CalendarEventBulkCreate(BaseModel):
    """Schema for creating multiple calendar events at once."""
    events: List[CalendarEventCreate]


class CalendarEventRead(CalendarEventBase):
    """Schema for reading a calendar event."""
    id: int
    student_id: int
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    class_id: Optional[int] = None
