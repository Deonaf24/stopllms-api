from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, get_db
from app.models.school import User, Class
from app.services.google_classroom import service as google_service
from app.schemas.school import ClassRead

router = APIRouter()

from app.services.school import classes as classes_service

@router.post("/google/sync/courses", response_model=list[ClassRead])
def sync_google_courses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually triggers a sync of Google Classroom courses.
    """
    if not current_user.is_teacher:
         raise HTTPException(status_code=403, detail="Only teachers can sync courses")
         
    classes = google_service.sync_courses(db, current_user)
    return [classes_service.class_to_schema(c) for c in classes]
