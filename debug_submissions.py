import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.school import StudentAssignment, Student, Assignment, User, Class
from app.core.config import settings
from app.services.google_classroom import GoogleClassroomService

# Setup DB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Ensure tables exist (Hack for dev: normally use Alembic)
from app.models.school import Base
Base.metadata.create_all(bind=engine)

def debug_submissions():
    print("--- Debugging Submissions ---")
    
    # 1. Check if any StudentAssignments exist
    count = db.query(StudentAssignment).count()
    print(f"Total StudentAssignment records: {count}")
    
    if count > 0:
        assignments = db.query(StudentAssignment).all()
        for sa in assignments[:5]:
            print(f"  SA: Student {sa.student_id}, Asgn {sa.assignment_id}, Status: {sa.status}")
    else:
        print("  (No records found)")

    # 2. Try to sync for the first class/assignment found
    user_email = "deon.aftahi@gmail.com" # Hardcoded for debugging as per previous context
    user = db.query(User).filter(User.email == user_email).first()
    
    if not user:
        print(f"User {user_email} not found.")
        return

    print(f"User found: {user.email}")
    
    # Get a class
    clazz = db.query(Class).filter(Class.google_id != None).first()
    if not clazz:
        print("No Google-linked class found.")
        return
        
    print(f"Class: {clazz.name} ({clazz.google_id})")
    
    # Get an assignment
    asgn = db.query(Assignment).filter(Assignment.class_id == clazz.id, Assignment.google_id != None).first()
    if not asgn:
        print("No Google-linked assignment found.")
        return

    print(f"Assignment: {asgn.title} ({asgn.google_id})")
    
    # Trigger Sync Logic manually
    # service = GoogleClassroomService()
    # print("Runing sync_assignment...")
    # try:
    #     service.sync_assignment(db, user, asgn.id)
    #     # db.commit() # sync_assignment commits internally
    #     print("Sync finished.")
        
    #     # Check records again
    #     all_subs = db.query(StudentAssignment).filter(
    #         StudentAssignment.assignment_id == 22
    #     ).all()
        
    #     print(f"Submissions for Assignment {asgn.title}: {len(all_subs)}")
    #     for s in all_subs:
    #         student = db.query(Student).filter(Student.user_id == s.student_id).first()
    #         print(f"  Student: {student.name} ({s.student_id}) -> Status: {s.status}")
            
    # except Exception as e:
    #     print(f"Sync failed: {e}")

if __name__ == "__main__":
    debug_submissions()
