import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.services.google_classroom.courses import GoogleCourseService
from app.models.school import User, Teacher, Class

@pytest.fixture
def mock_services():
    auth = MagicMock()
    assign = MagicMock()
    roster = MagicMock()
    return auth, assign, roster

@pytest.fixture
def gc_service(mock_services):
    return GoogleCourseService(*mock_services)

def test_sync_courses_creates_new_class(db_session: Session, gc_service, mock_services):
    auth_mock, assign_mock, roster_mock = mock_services
    
    # 1. Setup User (Teacher)
    user = User(email="gc_teach@school.com", hashed_password="pw", google_refresh_token="ref_tok")
    db_session.add(user)
    db_session.commit()
    teacher = Teacher(user_id=user.id, name="GC Teacher", email="gc_teach@school.com")
    db_session.add(teacher)
    db_session.commit()
    
    # 2. Mock Google API Response
    mock_service_obj = MagicMock()
    auth_mock.build_service.return_value = mock_service_obj
    
    # service.courses().list().execute()
    mock_courses_list = mock_service_obj.courses.return_value.list.return_value.execute
    mock_courses_list.return_value = {
        "courses": [
            {"id": "g_123", "name": "Google Math", "description": "Desc", "ownerId": "me"}
        ]
    }
    
    # 3. Execute Sync
    synced = gc_service.sync_courses(db_session, user)
    
    # 4. Verify
    assert len(synced) == 1
    new_class = synced[0]
    assert new_class.name == "Google Math"
    assert new_class.google_id == "g_123"
    assert new_class.teacher_id == teacher.id
    assert new_class.is_google_synced is True
    
    # Verify sub-syncs called
    assign_mock.sync_course_work.assert_called_once()
    roster_mock.sync_roster.assert_called_once()

def test_sync_courses_updates_existing_class(db_session: Session, gc_service, mock_services):
    auth_mock, _, _ = mock_services
    
    # 1. Setup User & Existing Class
    user = User(email="gc_teach2@school.com", hashed_password="pw", google_refresh_token="ref_tok")
    db_session.add(user)
    db_session.commit()
    teacher = Teacher(user_id=user.id, name="GC Teacher 2", email="gc_teach2@school.com")
    db_session.add(teacher)
    db_session.commit()
    
    # Existing class with old name
    existing = Class(
        name="Old Name", 
        google_id="g_456", 
        teacher_id=teacher.id, 
        join_code="OLD", 
        is_google_synced=True
    )
    db_session.add(existing)
    db_session.commit()
    
    # 2. Mock Google API (New Name)
    mock_service_obj = MagicMock()
    auth_mock.build_service.return_value = mock_service_obj
    mock_courses_list = mock_service_obj.courses.return_value.list.return_value.execute
    mock_courses_list.return_value = {
        "courses": [
            {"id": "g_456", "name": "New Google Name", "description": "Desc", "ownerId": "me"}
        ]
    }
    
    # 3. Execute
    synced = gc_service.sync_courses(db_session, user)
    
    # 4. Verify
    db_session.refresh(existing)
    assert existing.name == "New Google Name"
    assert len(synced) == 1
