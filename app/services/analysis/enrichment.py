from app.models.school import Assignment, Student, User

def enrich_assignment(assignment: Assignment):
    """
    Analyzes the assignment content and tags it with concepts.
    """
    # TODO: Implement LLM analysis here
    print(f"Enriching assignment: {assignment.title}")
    pass

def enrich_student_profile(student: Student, submission_content: str):
    """
    Analyzes the student submission and updates understanding scores.
    """
    # TODO: Implement LLM analysis here
    print(f"Enriching profile for student: {student.name}")
    pass
