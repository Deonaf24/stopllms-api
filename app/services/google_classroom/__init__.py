from .auth import GoogleAuthService
from .drive import GoogleDriveService
from .roster import GoogleRosterService
from .assignments import GoogleAssignmentService
from .submissions import GoogleSubmissionService
from .courses import GoogleCourseService

class GoogleClassroomService:
    def __init__(self):
        self.auth = GoogleAuthService()
        self.drive = GoogleDriveService(self.auth)
        self.roster = GoogleRosterService(self.auth)
        self.submissions = GoogleSubmissionService(self.auth)
        self.assignments = GoogleAssignmentService(self.auth, self.drive, self.submissions)
        self.courses = GoogleCourseService(self.auth, self.assignments, self.roster)

    # Proxy methods for backward compatibility
    # These match the previous "God Class" public API

    def build_service(self, refresh_token: str, service_name="classroom", version="v1"):
        return self.auth.build_service(refresh_token, service_name, version)
        
    def list_courses(self, refresh_token: str):
        return self.courses.list_courses(refresh_token)

    def sync_courses(self, db, user):
        return self.courses.sync_courses(db, user)

    def sync_assignment(self, db, user, assignment_id):
        return self.submissions.sync_assignment(db, user, assignment_id)

    def exchange_code_for_token(self, code: str):
        return self.auth.exchange_code_for_token(code)
        
    # Exposing sub-services if needed directly, but usually we just use the facade methods above for now.

# Singleton instance
service = GoogleClassroomService()
