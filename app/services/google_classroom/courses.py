from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.school import Class, User
from app.services.google_classroom.converters import convert_course_to_class_dict

class GoogleCourseService:
    def __init__(self, auth_service, assignment_service, roster_service):
        self.auth = auth_service
        self.assignments = assignment_service
        self.roster = roster_service

    def list_courses(self, refresh_token: str) -> List[Dict[str, Any]]:
        try:
            service = self.auth.build_service(refresh_token)
            results = service.courses().list(courseStates=["ACTIVE"]).execute()
            return results.get("courses", [])
        except Exception as e:
            print(f"Error listing courses: {e}")
            return []

    def sync_courses(self, db: Session, user: User):
        """
        Syncs all ACTIVE courses from Google to local DB.
        """
        if not user.google_refresh_token:
            return []

        google_courses = self.list_courses(user.google_refresh_token)
        synced_classes = []
        
        teacher = user.teacher_link
        student = user.student_link

        if not teacher and not student:
            return []

        for g_course in google_courses:
            # Check if class exists
            existing_class = db.query(Class).filter(Class.google_id == g_course["id"]).first()
            
            # Helper to get teacher_id if we are the teacher
            current_teacher_id = teacher.id if teacher else (existing_class.teacher_id if existing_class else None)

            # Use converter
            class_data = convert_course_to_class_dict(g_course, teacher_id=current_teacher_id)

            if existing_class:
                if teacher:
                     existing_class.name = class_data["name"]
                     existing_class.is_google_synced = True
                
                synced_classes.append(existing_class)
                
                # If Teacher, sync work
                if teacher:
                    self.assignments.sync_course_work(db, user, g_course["id"], existing_class.id)
                    self.roster.sync_roster(db, user, g_course["id"], existing_class.id)

            else:
                # Create new class
                import secrets
                join_code = secrets.token_hex(3).upper() # Fallback

                new_class = Class(
                    name=class_data["name"],
                    description=class_data.get("description"),
                    google_id=class_data["google_id"],
                    join_code=join_code, 
                    teacher_id=class_data["teacher_id"], 
                    is_google_synced=True
                )
                
                try:
                    with db.begin_nested():
                        db.add(new_class)
                        db.flush() # Flush to get ID
                    synced_classes.append(new_class)
                    existing_class = new_class
                except IntegrityError:
                    print(f"Race condition detected for course {g_course['id']}, re-fetching.")
                    existing_class = db.query(Class).filter(Class.google_id == g_course["id"]).first()
                    if existing_class:
                        synced_classes.append(existing_class)
                    else:
                        print(f"Failed to recover existing class for {g_course['id']}")
                        continue
                
                # If Teacher, sync work
                if teacher:
                    self.assignments.sync_course_work(db, user, g_course["id"], new_class.id)
                    self.roster.sync_roster(db, user, g_course["id"], new_class.id)

            # ENROLLMENT LOGIC
            if student:
                # Check if already enrolled
                if student not in existing_class.students:
                    existing_class.students.append(student)

            # Student needs assignments too
            if student:
                 self.assignments.sync_course_work(db, user, g_course["id"], existing_class.id)

        db.commit()
        for c in synced_classes:
            db.refresh(c)
            
        return synced_classes
