
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import sys
import os
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.db import SessionLocal
from app.models.school import User, Teacher, Class, Student, LiveSession, LiveQuestion, LiveResponse, UnderstandingScore
from app.services.live_events import start_session, end_session, submit_answer, get_next_question_for_student, get_session_stats

def verify():
    db = SessionLocal()
    print("Verifying Self-Paced Flow...")

    try:
        # cleanup
        db.query(LiveSession).delete()
        db.query(Class).delete()
        db.query(Teacher).delete()
        db.query(Student).delete()
        db.query(User).delete()
        db.commit()

        # 1. Setup Data
        teacher_user = User(username="t_test", email="t@test.com", hashed_password="pw")
        teacher = Teacher(name="Mr. Test", email="t@test.com", user_account=teacher_user)
        
        student_user_a = User(username="s_a", email="a@test.com", hashed_password="pw")
        student_a = Student(name="Alice", email="a@test.com", user_account=student_user_a)

        student_user_b = User(username="s_b", email="b@test.com", hashed_password="pw")
        student_b = Student(name="Bob", email="b@test.com", user_account=student_user_b)

        my_class = Class(name="Math 101", join_code="MATH01", teacher=teacher, students=[student_a, student_b])
        
        db.add_all([teacher, student_a, student_b, my_class])
        db.commit()

        # 2. Create Session manually (mimic generation)
        session = LiveSession(class_id=my_class.id, status="active", concept_ids=[101, 102])
        q1 = LiveQuestion(text="2+2?", question_type="multiple_choice", options=["3", "4"], correct_answer="4", order=0, session=session)
        q2 = LiveQuestion(text="Capital of France?", question_type="multiple_choice", options=["Paris", "London"], correct_answer="Paris", order=1, session=session)
        
        db.add(session)
        db.commit()
        
        print(f"Session created: ID {session.id}")

        # 3. Test Flow - Student A
        next_q_a = get_next_question_for_student(db, session.id, student_a.id)
        print(f"Student A Next Q: {next_q_a.text if next_q_a else 'None'}")
        assert next_q_a.id == q1.id

        # Submit Answer A (Correct)
        submit_answer(db, q1.id, student_a.id, "4", time_spent_seconds=10)
        print("Student A answered Q1 (Correct, 10s)")

        # Test Flow - Student B
        next_q_b = get_next_question_for_student(db, session.id, student_b.id)
        assert next_q_b.id == q1.id # Both start at Q1

        # Submit Answer B (Incorrect)
        submit_answer(db, q1.id, student_b.id, "3", time_spent_seconds=5)
        print("Student B answered Q1 (Incorrect, 5s)")

        # Check Next Question logic
        next_q_a_2 = get_next_question_for_student(db, session.id, student_a.id)
        print(f"Student A Next Q: {next_q_a_2.text if next_q_a_2 else 'None'}")
        assert next_q_a_2.id == q2.id # A moves to Q2

        next_q_b_2 = get_next_question_for_student(db, session.id, student_b.id)
        assert next_q_b_2.id == q2.id # B moves to Q2

        # Check Stats
        stats = get_session_stats(db, session.id)
        q1_stats = next(s for s in stats['questions'] if s['question_id'] == q1.id)
        print(f"Q1 Stats: {q1_stats['distribution']}")
        assert q1_stats['distribution']['4'] == 1
        assert q1_stats['distribution']['3'] == 1

        # 4. End Session & Analytics
        end_session(db, session.id)
        print("Session ended.")

        # Check Understanding Scores
        # Student A: 1 correct out of 2 (assuming they stopped after Q1? No, total questions is 2. So score is 50%)
        # Logic: 1 correct / 2 total = 50%
        scores_a = db.query(UnderstandingScore).filter(UnderstandingScore.student_id == student_a.id).all()
        print(f"Student A Analytics Created: {len(scores_a)}")
        for s in scores_a:
            print(f" - Concept {s.concept_id}: {s.score}% (Source: {s.source})")
            assert s.score == 50.0

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify()
