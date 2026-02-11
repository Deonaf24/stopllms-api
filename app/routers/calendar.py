from datetime import datetime, timedelta, date, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.calendar import CalendarEvent
from app.models.school import Student
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventRead,
    CalendarEventBulkCreate,
    CalendarEventUpdate,
)

from app.models.school import Student, Teacher

router = APIRouter(tags=["calendar"])
student_router = APIRouter(prefix="/students/{student_id}/calendar-events")
teacher_router = APIRouter(prefix="/teachers/{teacher_id}/calendar-events")


def get_student_or_404(db: Session, student_id: int) -> Student:
    """Helper to get student or raise 404."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    return student

def get_teacher_or_404(db: Session, teacher_id: int) -> Teacher:
    """Helper to get teacher or raise 404."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher {teacher_id} not found"
        )
    return teacher


@student_router.post("/", response_model=List[CalendarEventRead], status_code=status.HTTP_201_CREATED)
def create_calendar_events(
    student_id: int,
    payload: CalendarEventBulkCreate,
    db: Session = Depends(get_db),
):
    """Create multiple calendar events for a student."""
    get_student_or_404(db, student_id)
    
    created_events = []
    for event_data in payload.events:
        event = CalendarEvent(
            student_id=student_id,
            title=event_data.title,
            description=event_data.description,
            start_at=event_data.start_at,
            end_at=event_data.end_at,
            class_id=event_data.class_id,
            source=event_data.source,
        )
        db.add(event)
        created_events.append(event)
    
    db.commit()
    for event in created_events:
        db.refresh(event)
    
    return created_events



def _generate_lecture_events(user_obj: Student | Teacher, start_range: datetime, end_range: datetime) -> List[CalendarEventRead]:
    events = []
    if not start_range: start_range = datetime.now()
    if not end_range: end_range = start_range + timedelta(days=30)
    
    for cls in user_obj.classes:
        if not cls.lectures: continue
        
        c_start = cls.start_date
        c_end = cls.end_date
        
        q_start_date = start_range.date()
        q_end_date = end_range.date()
        
        actual_start = q_start_date
        if c_start and c_start > actual_start: actual_start = c_start
            
        actual_end = q_end_date
        if c_end and c_end < actual_end: actual_end = c_end
            
        if actual_start > actual_end: continue

        current = actual_start
        while current <= actual_end:
            dow = current.weekday()
            
            for lecture in cls.lectures:
                if lecture.day_of_week == dow:
                    start_dt = datetime.combine(current, lecture.start_time).astimezone()
                    end_dt = start_dt + timedelta(minutes=lecture.duration_minutes)
                    
                    fake_id = -abs(hash(f"lec_{lecture.id}_{current}")) % 10000000
                    
                    events.append(CalendarEventRead(
                        id=fake_id,
                        student_id=user_obj.id if isinstance(user_obj, Student) else 0, # Hack for now, CalendarEventRead needs student_id?
                        title=f"Lecture: {cls.name}",
                        description=f"Class Lecture for {cls.name}",
                        start_at=start_dt,
                        end_at=end_dt,
                        class_id=cls.id,
                        source="lecture",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ))
            
            current += timedelta(days=1)
            
    return events


@student_router.get("/", response_model=List[CalendarEventRead])
def list_calendar_events(
    student_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter events starting after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events ending before this date"),
    db: Session = Depends(get_db),
):
    """List calendar events for a student, optionally filtered by date range."""
    student = get_student_or_404(db, student_id)
    
    query = db.query(CalendarEvent).filter(CalendarEvent.student_id == student_id)
    
    if start_date:
        query = query.filter(CalendarEvent.start_at >= start_date)
    if end_date:
        query = query.filter(CalendarEvent.end_at <= end_date)
    
    db_events = query.order_by(CalendarEvent.start_at).all()
    results = [CalendarEventRead.model_validate(e) for e in db_events]
    
    # Generate lectures
    # Provide default range if None
    s_date = start_date or datetime.now()
    e_date = end_date or (s_date + timedelta(days=365)) # Default 1 year lookahead if unbounded? Or 30 days?
    # User usually requests specific range.
    
    lectures = _generate_lecture_events(student, s_date, e_date)
    results.extend(lectures)
    
    # Sort combined
    results.sort(key=lambda x: x.start_at)
    
    return results


@student_router.get("/{event_id}", response_model=CalendarEventRead)
def get_calendar_event(
    student_id: int,
    event_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific calendar event."""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.student_id == student_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    return event


@student_router.patch("/{event_id}", response_model=CalendarEventRead)
def update_calendar_event(
    student_id: int,
    event_id: int,
    payload: CalendarEventUpdate,
    db: Session = Depends(get_db),
):
    """Update a calendar event."""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.student_id == student_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    return event


@student_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(
    student_id: int,
    event_id: int,
    db: Session = Depends(get_db),
):
    """Delete a calendar event."""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.student_id == student_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    
@teacher_router.get("/", response_model=List[CalendarEventRead])
def list_teacher_calendar_events(
    teacher_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter events starting after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events ending before this date"),
    db: Session = Depends(get_db),
):
    """List calendar events for a teacher (lectures only for now)."""
    teacher = get_teacher_or_404(db, teacher_id)
    
    # Teachers don't have personal calendar events in DB yet (model limitation)
    # So we only generate lectures.
    
    s_date = start_date or datetime.now()
    e_date = end_date or (s_date + timedelta(days=365))
    
    lectures = _generate_lecture_events(teacher, s_date, e_date)
    
    results = lectures
    results.sort(key=lambda x: x.start_at)
    
    return results

router.include_router(student_router)
router.include_router(teacher_router)
