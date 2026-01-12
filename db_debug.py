import sys
import os

# Add the current directory to sys.path so we can import app
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.core.db import SessionLocal
from app.models.school import Assignment, UnderstandingScore, Student
from sqlalchemy import func
from app.services import analytics as analytics_service

def debug():
    db = SessionLocal()
    try:
        print("Checking Database State...")
        
        # Check Assignments
        assignment_count = db.query(Assignment).count()
        print(f"Total Assignments: {assignment_count}")
        
        assignments = db.query(Assignment).all()
        for a in assignments:
            print(f"- Assignment ID: {a.id}, Title: {a.title}")

        # Check Scores
        score_count = db.query(UnderstandingScore).count()
        print(f"Total Understanding Scores: {score_count}")
        
        # Check Students
        student_count = db.query(Student).count()
        print(f"Total Students: {student_count}")

        if assignment_count > 0:
            first_assignment_id = assignments[0].id
            print(f"\nTesting analytics for Assignment ID: {first_assignment_id}")
            
            # Check Chat Logs
            from app.models.school import ChatLog
            chat_log_count = db.query(ChatLog).filter(ChatLog.assignment_id == first_assignment_id).count()
            print(f"Chat Logs for Assignment {first_assignment_id}: {chat_log_count}")

            try:
                # Simulate "Generate Analytics" button click
                from app.services.analysis import score_assignment_understanding
                import asyncio
                print("Simulating scoring trigger...")
                # score_assignment_understanding is async, so we need to run it
                assignment = db.query(Assignment).get(first_assignment_id)
                # We can't easily run async in this sync script without event loop, but we can check if it works by just running it if it wasn't async, or just inspecting existing scores if we assume the button works.
                # Actually, let's just inspect if there are ANY understanding scores now?
                # The user wants to see analytics showing up.
                # Let's try to run the async function if possible, or just mock the data creation for verification.
                # Better yet, let's create a separate small async script to run it properly.
                
                analytics = analytics_service.get_assignment_analytics(db, first_assignment_id)
                print("Analytics Result:")
                print(analytics)
            except Exception as e:
                print(f"Error fetching analytics: {e}")
                import traceback
                traceback.print_exc()
        else:
             print("No assignments found.")

    finally:
        db.close()

if __name__ == "__main__":
    debug()
