from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import User
from app.core.config import settings

from app.core.db import SessionLocal # Import the session/connection logic
from app.models.school import User as UserModel # Import the SQLAlchemy User model
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Helper function to get the user model from the DB
def get_user_from_db(username: str) -> UserModel | None:
    """Queries the database for a user by username."""
    with SessionLocal() as db:
        answer = db.query(UserModel).filter(UserModel.username == username).first()
        return answer


def get_user(username: str):
    db = SessionLocal()

    user = (
        db.query(UserModel)
        .options(selectinload(UserModel.teacher_link))
        .options(selectinload(UserModel.student_link))
        .filter(UserModel.username == username)
        .first()
    )

    return user  # <-- RETURN THE SQLALCHEMY MODEL

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
    
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encode_jwt