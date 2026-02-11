from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .school import TimestampMixin


class CalendarEvent(TimestampMixin, Base):
    """
    User-created calendar events (e.g., from study plans).
    Includes google_event_id field for future Google Calendar sync.
    """
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Owner
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    
    # Optional class association
    class_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Timing
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Future: Google Calendar integration
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Source tracking (e.g., "study_plan", "manual")
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student")
    class_: Mapped["Class"] = relationship("Class")

    def __repr__(self) -> str:
        return f"<CalendarEvent id={self.id} title={self.title!r}>"
