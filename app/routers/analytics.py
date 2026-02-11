from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user
from app.models.school import User
from app.schemas.analytics import (
    AssignmentAnalyticsRead,
    ClassAnalyticsRead,
    StudentAnalyticsRead,
    ChapterAnalyticsRead
)
from app.services.analysis import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/students/{student_id}", response_model=StudentAnalyticsRead)
def get_student_analytics(student_id: int, db: Session = Depends(get_db)):
    return analytics_service.get_student_analytics(db, student_id)


@router.get("/assignments/{assignment_id}", response_model=AssignmentAnalyticsRead)
def get_assignment_analytics(assignment_id: int, db: Session = Depends(get_db)):
    assignment = analytics_service.ensure_assignment_exists(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return analytics_service.get_assignment_analytics(db, assignment_id)




@router.get("/classes/{class_id}/chapters", response_model=list[ChapterAnalyticsRead])
def get_class_chapter_analytics(
    class_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    class_obj = analytics_service.ensure_class_exists(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # If student, return their specific analytics
    if current_user.student_link:
        return analytics_service.get_chapter_analytics(db, class_id, current_user.student_link.id)
    
    # If teacher/admin, return class stats
    return analytics_service.get_class_chapter_stats(db, class_id)
@router.get("/classes/{class_id}", response_model=ClassAnalyticsRead)
def get_class_analytics(class_id: int, db: Session = Depends(get_db)):
    class_obj = analytics_service.ensure_class_exists(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return analytics_service.get_class_analytics(db, class_id)
