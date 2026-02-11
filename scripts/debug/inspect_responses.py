
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.school import LiveSession, LiveQuestion, LiveResponse

def inspect_data():
    db = SessionLocal()
    try:
        # Get latest session
        session = db.query(LiveSession).order_by(LiveSession.id.desc()).first()
        if not session:
            print("No sessions found.")
            return

        print(f"Session ID: {session.id}, Status: {session.status}")
        
        # Get questions
        questions = db.query(LiveQuestion).filter(LiveQuestion.session_id == session.id).all()
        print(f"Found {len(questions)} questions.")

        for q in questions:
            print(f"Question {q.id} ({q.question_type}): {q.text[:50]}...")
            # Get responses
            responses = db.query(LiveResponse).filter(LiveResponse.question_id == q.id).all()
            print(f"  > Responses: {len(responses)}")
            for r in responses:
                print(f"    - Resp {r.id}: Answer='{r.answer}', is_correct={r.is_correct} (Type: {type(r.is_correct)})")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_data()
