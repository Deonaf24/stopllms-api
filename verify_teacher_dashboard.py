import asyncio
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.core.db import SessionLocal
from app.services.live_events import (
    generate_live_event_prompt, 
    start_session, 
    end_session, 
    submit_answer, 
    next_question,
    get_session_stats
)
from app.schemas.live_events import LiveQueryRequest

async def verify():
    # Mock return value
    mock_json = """
    {
      "questions": [
        {
          "id": 1,
          "text": "Q1",
          "options": ["A", "B", "C", "D"],
          "correct_answer": "A",
          "explanation": "Exp 1"
        },
        {
          "id": 2,
          "text": "Q2",
          "options": ["True", "False"],
          "correct_answer": "True",
          "explanation": "Exp 2"
        }
      ]
    }
    """
    
    print("Starting verification of Teacher Dashboard Stats...")
    
    with patch('app.services.live_events.generate_text', return_value=mock_json):
        db = SessionLocal()
        try:
            # 1. Generate & Start
            req = LiveQueryRequest(concept_ids=[6], question_type="multiple_choice")
            response = await generate_live_event_prompt(db, 2, req)
            session_id = response.session.id
            start_session(db, session_id)
            print(f"Session {session_id} started.")
            
            # 2. Q1: Submit Answers
            # Q1 Options: A, B, C, D
            # 2 votes for A, 1 for B
            q1_id = response.session.questions[0].id
            submit_answer(db, q1_id, 1, "A")
            submit_answer(db, q1_id, 2, "A")
            submit_answer(db, q1_id, 3, "B")
            print("Submitted 3 answers for Q1 (A, A, B).")
            
            # 3. Check Stats for Q1
            stats = get_session_stats(db, session_id)
            print(f"Stats Q1: Total={stats['total_responses']}, Distribution={stats['distribution']}")
            
            if stats['total_responses'] == 3 and stats['distribution'].get('A') == 2 and stats['distribution'].get('B') == 1:
                print("SUCCESS: Q1 Stats Correct.")
            else:
                print("FAILURE: Q1 Stats Incorrect.")
                
            # 4. Next Question
            next_question(db, session_id)
            print("Moved to Q2.")
            
            # 5. Check Stats for Q2 (Should be empty initially)
            stats_q2_initial = get_session_stats(db, session_id)
            print(f"Stats Q2 Initial: Total={stats_q2_initial['total_responses']}")
            if stats_q2_initial['total_responses'] == 0:
                print("SUCCESS: Q2 Stats Clean.")
            else:
                print("FAILURE: Q2 Stats not clean.")
                
            # 6. Q2: Submit Answers
            # Q2 Options: True, False
            q2_id = response.session.questions[1].id
            submit_answer(db, q2_id, 4, "True")
            print("Submitted 1 answer for Q2 (True).")
            
            stats_q2 = get_session_stats(db, session_id)
            print(f"Stats Q2: Distribution={stats_q2['distribution']}")
            if stats_q2['distribution'].get('True') == 1:
                 print("SUCCESS: Q2 Stats Correct.")
            
            # 7. End
            end_session(db, session_id)
            print("Session ended.")
            
        except Exception as e:
            print(f"Error during verification: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(verify())
