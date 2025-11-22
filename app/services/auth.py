from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
# Import all necessary models (assuming they are in app.models.school)
from app.models.school import User as UserModel, Teacher as TeacherModel, Student as StudentModel
from app.schemas.auth import User, UserCreate

def create_user(db: Session, user_in: UserCreate) -> UserModel:
    
    if db.query(UserModel).filter(UserModel.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    if db.query(UserModel).filter(UserModel.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # HASH THE PASSWORD
    hashed_password = get_password_hash(user_in.password)

    # 1. Create the base User (SQLAlchemy Model)
    # Note: 'is_teacher' is NOT a column on the User table, so it's not included here.
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        disabled=False,
    )
    
    # 2. Save base user to database and refresh to get the ID
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Now db_user has its ID (e.g., id=5)
    
    # 3. Create the profile link (Teacher or Student)
    if user_in.is_teacher:
        profile = TeacherModel(
            user_id=db_user.id,
            name=user_in.username, # Use username as default name
            email=user_in.email,
        )
    else:
        profile = StudentModel(
            user_id=db_user.id,
            name=user_in.username, # Use username as default name
            email=user_in.email,
        )
        
    db.add(profile)
    db.commit()
    # Refresh the user object again to load the newly created relationship (teacher_link or student_link)
    db.refresh(db_user) 
    
    # 4. Return the full User object. 
    # This object must now have the 'is_teacher' property (see Step 2 below)
    return db_user


def list_users(db: Session) -> list[User]:
    # Corrected to query UserModel
    return db.query(UserModel).all()


def get_user(db: Session, user_id: int) -> User | None:
    # Corrected to query UserModel
    return db.get(UserModel, user_id)

def delete_user(db: Session, user_id: int) -> User | None:
    # 1. Fetch the user instance using .get()
    user_to_delete = db.get(UserModel, user_id)

    if user_to_delete:
        # 2. Pass the instance to db.delete()
        db.delete(user_to_delete) 
        
        # 3. Commit the transaction to execute the DELETE statement
        db.commit()
        
        # 4. Return the deleted object (now detached)
        return user_to_delete
        
    return None