
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import os
import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.school import User, Class, Assignment

# Connect to DB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def get_user_credentials(db, email):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        print(f"User {email} not found")
        return None
    
    if not user.google_refresh_token:
        print("User has no refresh token")
        return None
        
    return Credentials(
        token=None,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

def inspect_materials(email, course_name="test"):
    creds = get_user_credentials(db, email)
    if not creds:
        return

    service = build("classroom", "v1", credentials=creds)
    
    # 1. Find the course
    courses = service.courses().list(courseStates=["ACTIVE"]).execute().get("courses", [])
    target_course = None
    for c in courses:
        if c.get("name").lower() == course_name.lower():
            target_course = c
            break
            
    if not target_course:
        print(f"Course '{course_name}' not found. Available: {[c.get('name') for c in courses]}")
        return

    print(f"Found Course: {target_course.get('name')} ({target_course.get('id')})")
    
    # 2. List CourseWork
    course_work = service.courses().courseWork().list(courseId=target_course.get("id")).execute().get("courseWork", [])
    
    print(f"Found {len(course_work)} assignments.")
    
    for work in course_work:
        print(f"\nAssignment: {work.get('title')} ({work.get('id')})")
        materials = work.get("materials", [])
        print(f"Materials Count: {len(materials)}")
        print(json.dumps(materials, indent=2))
        
        # Check specific materials logic
        for material in materials:
            drive_file = material.get("driveFile", {}).get("driveFile")
            if drive_file:
                file_id = drive_file.get("id")
                print(f" -> Found Drive File: {drive_file.get('title')} (ID: {file_id})")
                
                # Try downloading
                print("    Attempting download...")
                try:
                    drive_service = build("drive", "v3", credentials=creds)
                    # Check for google apps mime types
                    meta = drive_service.files().get(fileId=file_id, fields="mimeType").execute()
                    if meta.get("mimeType").startswith("application/vnd.google-apps"):
                        print("    Skipping download (Google Doc/Sheet/Slide)")
                        continue
                        
                    request = drive_service.files().get_media(fileId=file_id)
                    content = request.execute()
                    print(f"    SUCCESS: Downloaded {len(content)} bytes.")
                except Exception as e:
                    print(f"    FAILURE: Could not download. Error: {e}")

if __name__ == "__main__":
    inspect_materials("deon.aftahi@gmail.com", "test")
