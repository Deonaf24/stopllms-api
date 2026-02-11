
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.core.db import SessionLocal
from app.services.live_events import generate_live_event_prompt, start_session, end_session, get_active_session_for_class
from app.schemas.live_events import LiveQueryRequest
from app.models.school import LiveSession

async def verify():
    # Mock return value
    mock_json = """
    {
      "questions": [{"id": 1, "text": "Q1", "options": ["A"], "correct_answer": "A", "explanation": "E"}]
    }
    """
    
    print("Starting verification of Active Session Lookup...")
    
    with patch('app.services.live_events.generate_text', return_value=mock_json):
        db = SessionLocal()
        try:
            # 1. Generate & Start Session for Class 2
            req = LiveQueryRequest(concept_ids=[6], question_type="multiple_choice")
            response = await generate_live_event_prompt(db, 2, req)
            session_id = response.session.id
            start_session(db, session_id)
            print(f"Session {session_id} started for Class 2.")
            
            # 2. Check Active Session
            active_session = get_active_session_for_class(db, 2)
            if active_session and active_session.id == session_id:
                print(f"SUCCESS: Found active session {active_session.id} for Class 2.")
            else:
                print(f"FAILURE: Did not find active session. Found: {active_session}")
                
            # 3. End Session
            end_session(db, session_id)
            print("Session ended.")
            
            # 4. Check Active Session again
            active_session_after = get_active_session_for_class(db, 2)
            if active_session_after is None:
                print("SUCCESS: No active session found after ending.")
            else:
                print(f"FAILURE: Still found active session {active_session_after.id}")

        except Exception as e:
            print(f"Error during verification: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(verify())
