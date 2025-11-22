from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.school import User
from app.schemas.auth import User, UserCreate

def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(**user_in.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)