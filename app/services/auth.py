from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.school import User as UserModel
from app.schemas.auth import User, UserCreate

def create_user(db: Session, user_in: UserCreate) -> UserModel:
    
    if db.query(User).filter(UserModel.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # HASH THE PASSWORD
    hashed_password = get_password_hash(user_in.password)

    # 1. Prepare the data for the SQLAlchemy Model
    # We explicitly map fields and use the HASHED password.
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password, 
        disabled=False
    )
    
    # 2. Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def list_users(db: Session) -> list[User]:
    return db.query(User).all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)