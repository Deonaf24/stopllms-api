from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from app.core.security import authenticate_user, create_access_token
from app.core.deps import get_current_active_user
from app.schemas.auth import Token, User, UserCreate
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.schemas.school import StudentCreate, TeacherCreate
from app.services import auth as auth_service
from app.services import school as school_service
from app.core.db import SessionLocal

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print("authenticating")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/register", response_model=User)
async def register_user(new_user: UserCreate):
    with SessionLocal() as db:
        new_user_db = auth_service.create_user(db, new_user)
        if new_user.is_teacher:
            new_teacher = TeacherCreate(
            user_id=new_user_db.id,
            )
            school_service.create_teacher(db, new_teacher)
        else:
            new_student = StudentCreate(
                user_id=new_user_db.id
            )
            school_service.create_student(db, new_student)
        return new_user_db
