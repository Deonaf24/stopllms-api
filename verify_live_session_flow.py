import asyncio
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.core.db import SessionLocal
from app.services.live_events import generate_live_event_prompt, start_session, end_session, submit_answer, get_current_question
from app.schemas.live_events import LiveQueryRequest
from app.models.school import LiveSession

async def verify():
    # Mock return value
    mock_json = """
    {
      "questions": [
        {
          "id": 1,
          "text": "First Question?",
          "options": ["A", "B", "C", "D"],
          "correct_answer": "A",
          "explanation": "Exp 1"
        },
        {
          "id": 2,
          "text": "Second Question?",
          "options": ["X", "Y", "Z"],
          "correct_answer": "Z",
          "explanation": "Exp 2"
        }
      ]
    }
    """
    
    print("Starting verification with MOCKED LLM response...")
    
    with patch('app.services.live_events.generate_text', return_value=mock_json):
        db = SessionLocal()
        try:
            # 1. Generate
            req = LiveQueryRequest(
                concept_ids=[6, 7], 
                question_type="multiple_choice",
                time_limit=15
            )
            response = await generate_live_event_prompt(db, 2, req)
            session_id = response.session.id
            print(f"Session Created: ID={session_id}")
            
            # 2. Start
            print("Starting Session...")
            session = start_session(db, session_id)
            print(f"Session Status: {session.status}")
            
            # 3. Get Current Question (Index 0)
            q1 = get_current_question(db, session_id)
            print(f"Current Question 1: {q1.text} (ID: {q1.id})")
            
            # 4. Submit Answer (Student 5, correct)
            print(f"Submitting Answer 'A' for Student 5...")
            resp1 = submit_answer(db, q1.id, 5, "A")
            print(f"Response: Correct={resp1.is_correct} (Expected True)")
            
            # 5. Submit Answer (Student 6, wrong)
            print(f"Submitting Answer 'B' for Student 6...")
            resp2 = submit_answer(db, q1.id, 6, "B")
            print(f"Response: Correct={resp2.is_correct} (Expected False)")
            
            # 6. End Session
            print("Ending Session...")
            session = end_session(db, session_id)
            print(f"Session Status: {session.status}")
            
            print("SUCCESS: Flow verified.")
                
        except Exception as e:
            print(f"Error during verification: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(verify())
