import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import date

from app.services.school.live_events import generate_live_event_prompt
from app.schemas.live_events import LiveQueryRequest
from app.models.school import Class, Concept, User, Teacher

# We need a basic setup for the class and concepts
# Since we are testing SERVICE robustness, we can mock the DB query results 
# OR use the db_session fixture if it supports creating these objects.
# Using db_session is safer integration-like unit test.

@pytest.fixture
def ai_test_setup(db_session: Session):
    # 1. Create Teacher
    user = User(email="ai_test@school.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    
    teacher = Teacher(user_id=user.id, name="AI Teacher", email="ai_test@school.com")
    db_session.add(teacher)
    db_session.commit()

    # 2. Create Class
    class_obj = Class(
        name="AI Test Class",
        teacher_id=teacher.id,
        join_code="AITest",
        start_date=date.today(),
        end_date=date.today()
    )
    db_session.add(class_obj)
    db_session.commit()

    # 3. Create Concepts
    c1 = Concept(name="Robotics", description="Tech")
    c2 = Concept(name="Ethics", description="Phil")
    db_session.add_all([c1, c2])
    db_session.commit()
    
    return {
        "class_id": class_obj.id,
        "concept_ids": [c1.id, c2.id]
    }

@pytest.mark.asyncio
@patch("app.services.school.live_events.generate_text")
@patch("app.services.school.live_events.extract_content_from_files")
async def test_generate_live_event_malformed_json(mock_extract, mock_gen, db_session, ai_test_setup):
    # Setup
    mock_extract.return_value = ("Context", [])
    mock_gen.return_value = "I am sorry, I cannot generate JSON for this request." # Malformed
    
    req = LiveQueryRequest(concept_ids=ai_test_setup["concept_ids"], question_type=["multiple_choice"], time_limit=10)
    
    # Execute
    response = await generate_live_event_prompt(db_session, ai_test_setup["class_id"], req)
    
    # Assert
    # Should handle gracefully -> Empty questions list
    assert len(response.session.questions) == 0
    assert response.session.status == "active"

@pytest.mark.asyncio
@patch("app.services.school.live_events.generate_text")
@patch("app.services.school.live_events.extract_content_from_files")
async def test_generate_live_event_markdown_json(mock_extract, mock_gen, db_session, ai_test_setup):
    # Setup
    mock_extract.return_value = ("Context", [])
    # Valid JSON wrapped in markdown
    json_text = """
    ```json
    {
        "questions": [
            {
                "text": "What is 2+2?",
                "question_type": "multiple_choice",
                "options": ["3", "4", "5"],
                "correct_answer": "4"
            }
        ]
    }
    ```
    """
    mock_gen.return_value = json_text
    
    req = LiveQueryRequest(concept_ids=ai_test_setup["concept_ids"])
    
    # Execute
    response = await generate_live_event_prompt(db_session, ai_test_setup["class_id"], req)
    
    # Assert
    assert len(response.session.questions) == 1
    assert response.session.questions[0].text == "What is 2+2?"
    # correct_answer is excluded from the schema to prevent cheating
    # assert response.session.questions[0].correct_answer == "4"

@pytest.mark.asyncio
@patch("app.services.school.live_events.generate_text")
@patch("app.services.school.live_events.extract_content_from_files")
async def test_generate_live_event_empty_json(mock_extract, mock_gen, db_session, ai_test_setup):
    # Setup
    mock_extract.return_value = ("Context", [])
    mock_gen.return_value = "{}" # Valid JSON, but missing 'questions'
    
    req = LiveQueryRequest(concept_ids=ai_test_setup["concept_ids"])
    
    # Execute
    response = await generate_live_event_prompt(db_session, ai_test_setup["class_id"], req)
    
    # Assert
    assert len(response.session.questions) == 0

@pytest.mark.asyncio
@patch("app.services.school.live_events.generate_text")
@patch("app.services.school.live_events.extract_content_from_files")
async def test_generate_live_event_partial_json_crash(mock_extract, mock_gen, db_session, ai_test_setup):
    # Setup - Broken JSON (cut off)
    mock_extract.return_value = ("Context", [])
    mock_gen.return_value = '{"questions": [{"text": "Cut off...'
    
    req = LiveQueryRequest(concept_ids=ai_test_setup["concept_ids"])
    
    # Execute
    response = await generate_live_event_prompt(db_session, ai_test_setup["class_id"], req)
    
    # Assert - Should be 0 questions, no crash
    assert len(response.session.questions) == 0
