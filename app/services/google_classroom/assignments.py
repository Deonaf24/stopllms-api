from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import asyncio

from app.models.school import Class, User, Assignment, File
from app.services.google_classroom.converters import convert_coursework_to_assignment_dict
from app.services.storage import get_storage_service

class GoogleAssignmentService:
    def __init__(self, auth_service, drive_service, submission_service):
        self.auth = auth_service
        self.drive = drive_service
        self.submissions = submission_service

    def list_course_work(self, refresh_token: str, course_id: str) -> List[Dict[str, Any]]:
        try:
            service = self.auth.build_service(refresh_token)
            results = service.courses().courseWork().list(courseId=course_id).execute()
            return results.get("courseWork", [])
        except Exception as e:
            print(f"Error listing course work for {course_id}: {e}")
            return []

    def sync_course_work(self, db: Session, user: User, course_id: str, local_class_id: int):
        """
        Syncs assignments for a specific course.
        """
        if not user.google_refresh_token:
            return
        
        storage = get_storage_service()
        
        course_work_list = self.list_course_work(user.google_refresh_token, course_id)
        
        # Determine teacher ID for assignments
        current_teacher_id = None
        if user.teacher_link:
             current_teacher_id = user.teacher_link.id
        else:
             # Try to get from class
             local_class = db.query(Class).filter(Class.id == local_class_id).first()
             if local_class and local_class.teacher_id:
                 current_teacher_id = local_class.teacher_id

        for work in course_work_list:
            # Check if assignment exists
            existing_assignment = db.query(Assignment).filter(Assignment.google_id == work["id"]).first()
            
            # Use converter
            assignment_data = convert_coursework_to_assignment_dict(
                work, 
                class_id=local_class_id, 
                teacher_id=current_teacher_id
            )
            
            assignment_obj = None
            if existing_assignment:
                # Update allowed fields
                existing_assignment.title = assignment_data["title"]
                existing_assignment.description = assignment_data["description"]
                existing_assignment.google_link = assignment_data["google_link"]
                existing_assignment.due_at = assignment_data["due_at"]
                
                if current_teacher_id and not existing_assignment.teacher_id:
                    existing_assignment.teacher_id = current_teacher_id
                assignment_obj = existing_assignment
            else:
                new_assignment = Assignment(**assignment_data)
                db.add(new_assignment)
                db.flush() # Need ID for files
                assignment_obj = new_assignment
        
            # Handle Attachments (Materials)
            materials = work.get("materials", [])
            for material in materials:
                drive_file = material.get("driveFile", {}).get("driveFile")
                if not drive_file:
                    continue
                
                file_id = drive_file.get("id")
                file_title = drive_file.get("title")
                
                existing_file = db.query(File).filter(
                    File.assignment_id == assignment_obj.id,
                    File.filename == file_title
                ).first()
                
                if existing_file:
                    continue
                
                print(f"Downloading attachment: {file_title} ({file_id})")
                download_result = self.drive.download_drive_file(user.google_refresh_token, file_id)
                if not download_result:
                    continue
                
                content, filename, mime_type = download_result
                
                try:
                    # Bridge async storage call
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    stored = loop.run_until_complete(
                        storage.save_content(
                            filename=filename,
                            content=content,
                            mime_type=mime_type,
                            folder=f"assignments/{assignment_obj.id}"
                        )
                    )
                    loop.close()
                    
                    new_file = File(
                        filename=filename,
                        path=stored.path,
                        url=stored.url,
                        mime_type=mime_type,
                        size=stored.size,
                        assignment_id=assignment_obj.id
                    )
                    db.add(new_file)
                except Exception as e:
                    print(f"Failed to save attachment {file_title}: {e}")
            
            # Sync Submissions for this assignment
            self.submissions.sync_student_submissions(db, user, course_id, WorkID=work["id"], assignment_obj=assignment_obj)

        db.commit()
