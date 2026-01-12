from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from app.core.db import get_db
from app.models import school as models
from app.schemas import stream as schemas

router = APIRouter(
    prefix="/stream",
    tags=["stream"],
)

# --- Announcements ---

@router.post("/announcements", response_model=schemas.AnnouncementRead)
def create_announcement(
    announcement: schemas.AnnouncementCreate, 
    # In a real app, we'd get current_user here
    author_id: int, 
    db: Session = Depends(get_db)
):
    db_announcement = models.Announcement(
        title=announcement.title,
        content=announcement.content,
        class_id=announcement.class_id,
        author_id=author_id
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement

@router.get("/classes/{class_id}/announcements", response_model=List[schemas.AnnouncementRead])
def get_class_announcements(class_id: int, db: Session = Depends(get_db)):
    return db.query(models.Announcement)\
        .filter(models.Announcement.class_id == class_id)\
        .order_by(desc(models.Announcement.created_at))\
        .all()

# --- Polls ---

@router.post("/polls", response_model=schemas.PollRead)
def create_poll(
    poll: schemas.PollCreate,
    author_id: int,
    db: Session = Depends(get_db)
):
    # 1. Create Poll
    db_poll = models.Poll(
        title=poll.title,
        description=poll.description,
        question=poll.question,
        class_id=poll.class_id,
        author_id=author_id
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    # 2. Create Options
    for option_text in poll.options:
        db_option = models.PollOption(
            poll_id=db_poll.id,
            text=option_text
        )
        db.add(db_option)
    
    db.commit()
    db.refresh(db_poll)
    return db_poll

@router.get("/classes/{class_id}/polls", response_model=List[schemas.PollRead])
def get_class_polls(class_id: int, student_id: int = None, db: Session = Depends(get_db)):
    polls = db.query(models.Poll)\
        .filter(models.Poll.class_id == class_id)\
        .order_by(desc(models.Poll.created_at))\
        .all()

    # Enrich with vote counts and user status
    results = []
    for poll in polls:
        # Get vote counts per option
        options_data = []
        for option in poll.options:
            count = db.query(func.count(models.PollVote.id))\
                .filter(models.PollVote.option_id == option.id)\
                .scalar()
            
            # Pydantic model requires casting to correct shape, or we can rely on ORM -> Pydantic
            # But the 'vote_count' field is computed, not on the model directly unless added to schema mapped property
            # We'll create a dict to match schema
            options_data.append({
                "id": option.id,
                "poll_id": poll.id,
                "text": option.text,
                "vote_count": count
            })

        user_voted_option_id = None
        if student_id:
            vote = db.query(models.PollVote)\
                .filter(models.PollVote.poll_id == poll.id, models.PollVote.student_id == student_id)\
                .first()
            if vote:
                user_voted_option_id = vote.option_id

        results.append({
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "question": poll.question,
            "class_id": poll.class_id,
            "author_id": poll.author_id,
            "created_at": poll.created_at,
            "updated_at": poll.updated_at,
            "options": options_data,
            "user_voted_option_id": user_voted_option_id
        })

    return results

@router.post("/polls/vote")
def vote_poll(vote: schemas.VoteCreate, db: Session = Depends(get_db)):
    # Check if already voted
    existing_vote = db.query(models.PollVote)\
        .filter(models.PollVote.poll_id == vote.poll_id, models.PollVote.student_id == vote.student_id)\
        .first()

    if existing_vote:
        # Update vote
        existing_vote.option_id = vote.option_id
    else:
        # Create vote
        new_vote = models.PollVote(
            poll_id=vote.poll_id,
            option_id=vote.option_id,
            student_id=vote.student_id
        )
        db.add(new_vote)
    
    db.commit()
    return {"status": "success"}
