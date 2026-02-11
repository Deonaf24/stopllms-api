import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.core.db import SessionLocal
from app.models.school import Assignment
from app.services.analysis import score_assignment_understanding
from app.services import analytics as analytics_service

async def run_scoring():
    db = SessionLocal()
    try:
        assignment = db.query(Assignment).first()
        if not assignment:
            print("No assignment found")
            return

        print(f"Scoring assignment {assignment.id}...")
        try:
            scores = await score_assignment_understanding(db, assignment)
            print(f"Generated {len(scores)} scores.")
        except Exception as e:
            print(f"Scoring failed: {e}")
            import traceback
            traceback.print_exc()

        # Check analytics again
        analytics = analytics_service.get_assignment_analytics(db, assignment.id)
        print("Analytics Result After Scoring:")
        print(analytics)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_scoring())
