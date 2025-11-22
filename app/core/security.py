from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import User
from app.core.config import settings

from app.core.db import SessionLocal # Import the session/connection logic
from app.models.school import User as UserModel # Import the SQLAlchemy User model
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Helper function to get the user model from the DB
def get_user_from_db(username: str) -> UserModel | None:
    """Queries the database for a user by username."""
    with SessionLocal() as db:
        answer = db.query(UserModel).filter(UserModel.username == username).first()
        return answer

def get_user(username: str):
    """Fetches user data from the database and returns it as a Pydantic User schema."""
    # Open a new session to query the database
    with SessionLocal() as db:
        user_model = get_user_from_db(username)
        
        if user_model:
            # Convert the SQLAlchemy model data to Pydantic User schema
            return User(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.username, 
                hashed_password=user_model.hashed_password,
                disabled=user_model.disabled
            )
    return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_passowrd_hash(password):
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