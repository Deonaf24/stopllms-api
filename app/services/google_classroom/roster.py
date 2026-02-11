from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.school import Class, User, Student, class_students

class GoogleRosterService:
    def __init__(self, auth_service):
        self.auth = auth_service

    def list_students(self, refresh_token: str, course_id: str) -> List[Dict[str, Any]]:
        try:
            service = self.auth.build_service(refresh_token)
            results = service.courses().students().list(courseId=course_id).execute()
            return results.get("students", [])
        except Exception as e:
            print(f"Error listing students for {course_id}: {e}")
            return []

    def sync_roster(self, db: Session, user: User, course_id: str, local_class_id: int):
        """
        Syncs students for a specific course.
        Note: Only teachers can list students usually.
        """
        if not user.google_refresh_token:
            return

        google_students = self.list_students(user.google_refresh_token, course_id)
        
        local_class = db.query(Class).filter(Class.id == local_class_id).first()
        if not local_class:
            return

        for g_student in google_students:
            profile = g_student.get("profile", {})
            email = profile.get("emailAddress")
            if email:
                email = email.lower() # Normalize

            google_id = profile.get("id")
            name = profile.get("name", {}).get("fullName")

            if not email:
                continue

            # Check if User exists (Case Insensitive)
            from sqlalchemy import func
            existing_user = db.query(User).filter(func.lower(User.email) == email).first()
            
            if not existing_user:
                # Provision new user
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(20))
                
                # Split name
                parts = name.split(" ", 1)
                first = parts[0] if parts else ""
                last = parts[1] if len(parts) > 1 else ""

                existing_user = User(
                    email=email,
                    hashed_password=f"PROVISIONED_{password}", # In real app, hash it properly
                    first_name=first,
                    last_name=last,
                    disabled=False # They can login via Google later
                )
                db.add(existing_user)
                db.flush() # Get ID

            # Ensure Student Profile exists
            if not existing_user.student_link:
                new_student = Student(
                    user_id=existing_user.id,
                    name=name or existing_user.email,
                    email=existing_user.email,
                    google_id=google_id
                )
                db.add(new_student)
                db.flush()
                # Refresh user to see link?
                existing_user.student_link = new_student
            else:
                # Update google_id if missing
                if not existing_user.student_link.google_id and google_id:
                     existing_user.student_link.google_id = google_id

            # Enroll in class
            student_profile = existing_user.student_link
            
            # Check enrollment explicitly
            is_enrolled = db.query(class_students).filter(
                class_students.c.class_id == local_class.id,
                class_students.c.student_id == student_profile.id
            ).first()

            if not is_enrolled:
                local_class.students.append(student_profile)
        
        db.commit()
