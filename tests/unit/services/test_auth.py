from sqlalchemy.orm import Session
from app.services.auth import create_user, get_user_by_email
from app.schemas.auth import UserCreate

def test_create_user(db_session: Session):
    email = "test@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, first_name="Test", last_name="User", is_teacher=False)
    
    user = create_user(db_session, user_in)
    
    assert user.email == email
    assert hasattr(user, "hashed_password")
    assert user.hashed_password != password  # Should be hashed
    assert user.is_teacher is False

def test_get_user_by_email(db_session: Session):
    email = "findme@example.com"
    user_in = UserCreate(email=email, password="password", first_name="Find", last_name="Me", is_teacher=False)
    create_user(db_session, user_in)
    
    user = get_user_by_email(db_session, email)
    assert user is not None
    assert user.email == email
