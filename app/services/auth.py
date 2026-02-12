from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
# Import all necessary models (assuming they are in app.models.school)
from app.models.school import User as UserModel, Teacher as TeacherModel, Student as StudentModel
from app.schemas.auth import User, UserCreate, GoogleLoginRequest, Token
from app.services.google_classroom import service as google_classroom_service
import requests
import string
import secrets
from fastapi import BackgroundTasks
from app.core.config import settings
from app.core.security import create_access_token
from datetime import timedelta


def create_user(db: Session, user_in: UserCreate) -> UserModel:
    
    if user_in.username and db.query(UserModel).filter(UserModel.username == user_in.username).first():
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
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=hashed_password,
        disabled=False,
    )
    
    # 2. Save base user to database and refresh to get the ID
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Now db_user has its ID (e.g., id=5)
    
    full_name = f"{user_in.first_name} {user_in.last_name}"

    # 3. Create the profile link (Teacher or Student)
    if user_in.is_teacher:
        profile = TeacherModel(
            user_id=db_user.id,
            name=full_name, 
            email=user_in.email,
        )
    else:
        profile = StudentModel(
            user_id=db_user.id,
            name=full_name,
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

def get_user_by_email(db: Session, email: str) -> UserModel | None:
    return db.query(UserModel).filter(UserModel.email == email).first()


from app.core.db import SessionLocal

def run_background_sync(user_id: int):
    with SessionLocal() as db: # IMPORTANT: Need a new session context if running in background
        from app.services import auth as auth_service
        # Re-import to avoid circular issues if any, though here it's fine
        user = auth_service.get_user(db, user_id)
        if user and user.is_teacher:
            print(f"Starting background sync for user {user.email}")
            google_classroom_service.sync_courses(db, user)


def process_google_login(db: Session, login_request: GoogleLoginRequest, background_tasks: BackgroundTasks) -> Token:
    print(f"Received Google Login Request")
    
    email = None
    id_info = None
    refresh_token = None
    google_id = None
    
    # CASE 1: Code Flow (Preferred for Backend Sync)
    if login_request.code:
        try:
            token_data = google_classroom_service.exchange_code_for_token(login_request.code)
            # Fetch user info using the access token
            access_token = token_data["token"]
            refresh_token = token_data.get("refresh_token")
            
            response = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            id_info = response.json()
            email = id_info.get("email")
            google_id = id_info.get("id")
            
        except Exception as e:
             print(f"Code exchange failed: {e}")
             raise HTTPException(status_code=401, detail="Invalid Google Code")

    # CASE 2: ID Token Flow (Legacy / Frontend-only)
    elif login_request.id_token:
        try:
            # Verify the access token by fetching user info (Old way)
            response = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {login_request.id_token}"}
            )
            response.raise_for_status()
            id_info = response.json()
            email = id_info.get("email")
            google_id = id_info.get("id")
            
        except Exception as e:
            print(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid Google token")
    else:
        raise HTTPException(status_code=400, detail="Missing code or id_token")

    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain email")

    print(f"Verified Google User: {email}")

    # Check if user exists
    user = get_user_by_email(db, email=email)
    
    if not user:
        if not login_request.is_signup:
            print(f"User not found and is_signup=False. Rejecting login for: {email}")
            raise HTTPException(
                status_code=401, 
                detail="User not found. Please sign up first."
            )

        print(f"User not found, registering new user: {email}")
        first_name = id_info.get("given_name", "")
        last_name = id_info.get("family_name", "")
        
        # Generate random password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(20))
        
        new_user_data = UserCreate(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_teacher=login_request.is_teacher 
        )
        user = create_user(db, new_user_data)
    
    # Update Google Credentials if we got them (Syncing logic)
    if refresh_token:
        print(f"Updating Refresh Token for {user.email}")
        user.google_refresh_token = refresh_token
    
    if google_id:
        if user.teacher_link and hasattr(user.teacher_link, 'google_id'):
            user.teacher_link.google_id = google_id
        if user.student_link:
            user.student_link.google_id = google_id

    db.add(user)
    db.commit()
    db.refresh(user)

    # Trigger Background Sync
    # Note: run_background_sync needs to be importable or defined. 
    # Since we are in service, we can define a small helper or import carefully.
    # We'll define a standalone function or use the one we can move here.
    if user.google_refresh_token and user.is_teacher:
         # We need to pass the user ID, not the object, to avoid session detachment issues in bg task
         # BUT background tasks run after the response is sent.
         # Ideally we define the sync function in this file or imported from elsewhere.
         # For now, let's assume we move run_background_sync to this file too or similar.
         background_tasks.add_task(run_background_sync, user.id)

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

