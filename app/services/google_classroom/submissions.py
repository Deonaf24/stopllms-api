from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.school import Class, User, Assignment, Student, StudentAssignment

class GoogleSubmissionService:
    def __init__(self, auth_service):
        self.auth = auth_service

    def sync_student_submissions(self, db: Session, user: User, course_id: str, WorkID: str, assignment_obj: Assignment):
        """
        Syncs student submissions for a specific assignment.
        """
        try:
            service = self.auth.build_service(user.google_refresh_token, service_name="classroom", version="v1")
            submissions = service.courses().courseWork().studentSubmissions().list(
                courseId=course_id,
                courseWorkId=WorkID
            ).execute().get("studentSubmissions", [])

            for sub in submissions:
                user_id = sub.get("userId") # Google User ID of the student
                stats = sub.get("submissionHistory", [])
                state = sub.get("state") # CREATED, TURNED_IN, RETURNED, RECLAIMED_BY_STUDENT
                assigned_grade = sub.get("assignedGrade")
                
                # Find the student in our DB
                student = db.query(Student).filter(Student.google_id == user_id).first()
                if not student:
                    continue
                
                local_user_id = student.user_id
                
                existing_sub = db.query(StudentAssignment).filter(
                    StudentAssignment.assignment_id == assignment_obj.id,
                    StudentAssignment.student_id == local_user_id
                ).first()
                
                if existing_sub:
                    existing_sub.status = state
                    existing_sub.grade = float(assigned_grade) if assigned_grade else None
                else:
                    new_sub = StudentAssignment(
                        student_id=local_user_id,
                        assignment_id=assignment_obj.id,
                        google_submission_id=sub.get("id"),
                        status=state,
                        grade=float(assigned_grade) if assigned_grade else None
                    )
                    db.add(new_sub)
                    
        except Exception as e:
            print(f"Error syncing submissions for assignment {assignment_obj.title}: {e}")

    def sync_assignment(self, db: Session, user: User, assignment_id: int):
        """
        Syncs a single assignment and its submissions.
        """
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment or not assignment.google_id:
            return 
        
        if not user.google_refresh_token:
            return
            
        # Get course ID from class
        clazz = db.query(Class).filter(Class.id == assignment.class_id).first()
        if not clazz or not clazz.google_id:
            return

        try:
            # We don't strictly need to fetch the assignment details again just for submission sync,
            # unless we want to update the assignment metadata too. 
            # For this method, let's focus on submissions as that is the primary use case.
            
            # Sync submissions
            self.sync_student_submissions(db, user, clazz.google_id, assignment.google_id, assignment)
            db.commit()
            
        except Exception as e:
            print(f"Error syncing single assignment {assignment_id}: {e}")
