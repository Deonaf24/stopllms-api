from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

def parse_google_datetime(date_dict: Optional[Dict], time_dict: Optional[Dict]) -> Optional[datetime]:
    """
    Parses Google's split date/time dictionaries into a single UTC datetime.
    
    Google Date: {"year": 2023, "month": 12, "day": 1}
    Google Time: {"hours": 14, "minutes": 30, "seconds": 0, "nanos": 0}
    """
    if not date_dict:
        return None
        
    try:
        year = date_dict.get("year")
        month = date_dict.get("month")
        day = date_dict.get("day")
        
        if not (year and month and day):
            return None
            
        # Default to end of day if no time specified, or start? 
        # Usually assignments are due at 23:59:59 if unspecified in UI, but API logic varies.
        # Let's default to 23:59:59 local if time is missing? 
        # For simplicity and safety, if time is missing, we default to 23:59:59 UTC for now.
        
        hour = 23
        minute = 59
        second = 59
        
        if time_dict:
            hour = time_dict.get("hours", 0)
            minute = time_dict.get("minutes", 0)
            second = time_dict.get("seconds", 0)
            
        # Create naive datetime
        dt = datetime(year, month, day, hour, minute, second)
        
        # In a real app, we might check time_dict ("nanos") or user timezone settings.
        # Google API dates are typically in the timezone of the course creator, 
        # but the API response sometimes omits this info. 
        # We will treat it as UTC for consistency in DB, or naive. 
        # SQLAlchemy stores naive datetimes as if they are local/UTC depending on config.
        # Let's assume generic UTC for now.
        return dt # Naive, typically assumed UTC/server time in many backends
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None

def convert_course_to_class_dict(google_course: Dict[str, Any], teacher_id: int) -> Dict[str, Any]:
    """
    Maps a Google Course object to kwargs for the Class model.
    """
    import secrets
    
    # Generate a random join code if we don't have one internal yet. 
    # (The caller will likely handle the join_code logic if creating new vs updating)
    # But we return a safe default here just in case.
    fallback_join_code = secrets.token_hex(3).upper()

    return {
        "name": google_course.get("name", "Untitled Google Class"),
        # "description": google_course.get("descriptionHeading"), # Optional, uncomment if desired
        "google_id": google_course.get("id"),
        "teacher_id": teacher_id,
        "is_google_synced": True,
        # "join_code" is typically managed by the caller (create vs update)
    }

def convert_coursework_to_assignment_dict(
    work: Dict[str, Any], 
    class_id: int, 
    teacher_id: int
) -> Dict[str, Any]:
    """
    Maps a Google CourseWork object to kwargs for the Assignment model.
    """
    
    date_dict = work.get("dueDate")
    time_dict = work.get("dueTime")
    
    due_at = parse_google_datetime(date_dict, time_dict)
    
    return {
        "title": work.get("title", "Untitled Assignment"),
        "description": work.get("description"),
        "class_id": class_id,
        "teacher_id": teacher_id,
        "google_id": work.get("id"),
        "google_link": work.get("alternateLink"),
        "level": 1, # Default level
        "due_at": due_at,
        "structure_approved": False
    }
