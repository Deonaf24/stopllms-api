import random
from datetime import datetime, timedelta, date, time
from sqlalchemy import text
from app.core.db import SessionLocal, engine
from app.models.base import Base
from app.models.school import (
    User, Teacher, Student, Class, Assignment, 
    UnderstandingScore, ChatLog, Concept, assignment_concepts, Lecture, Chapter
)
from app.models.calendar import CalendarEvent
from app.core.security import get_password_hash

def seed():
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Starting seed...")

        # 1. Teacher
        print("Creating Teacher...")
        teacher_email = "mr_socratica@school.com"
        teacher_pw = "pw"
        
        teacher_user = User(
            username="mr_socratica",
            email=teacher_email,
            first_name="Mr",
            last_name="Socratica",
            hashed_password=get_password_hash(teacher_pw)
        )
        db.add(teacher_user)
        db.flush()

        teacher = Teacher(
            user_id=teacher_user.id, 
            name="Mr. Socratica",
            email=teacher_email
        )
        db.add(teacher)
        db.flush()

        # 2. Classes, Concepts & Chapters
        print("Creating Classes, Concepts and Chapters...")
        class_data = [
            {
                "name": "Algebra 101", 
                "lectures": [(0, 8, 0), (2, 8, 0), (4, 8, 0)],  # Mon/Wed/Fri 8:00 AM
                "chapters": [
                    {"title": "Introduction to Algebra", "concepts": ["Linear Equations"]},
                    {"title": "Quadratic Equations", "concepts": ["Quadratic Functions"]},
                    {"title": "Polynomial Operations", "concepts": ["Polynomials"]}
                ]
            },
            {
                "name": "World History", 
                "lectures": [(0, 9, 30), (2, 9, 30)],  # Mon/Wed 9:30 AM
                "chapters": [
                    {"title": "The Renaissance Era", "concepts": ["The Renaissance"]},
                    {"title": "The Age of Industry", "concepts": ["Industrial Revolution"]},
                    {"title": "Modern Conflicts", "concepts": ["Cold War"]}
                ]
            },
            {
                "name": "Physics I", 
                "lectures": [(1, 10, 0), (3, 10, 0)],  # Tue/Thu 10:00 AM
                "chapters": [
                    {"title": "Motion and Kinematics", "concepts": ["Kinematics"]},
                    {"title": "Forces and Newton's Laws", "concepts": ["Newton's Laws"]},
                    {"title": "Work and Energy", "concepts": ["Energy Conservation"]}
                ]
            },
            {
                "name": "Literature 101", 
                "lectures": [(1, 13, 0), (3, 13, 0)],  # Tue/Thu 1:00 PM
                "chapters": [
                    {"title": "The Bard: Shakespeare", "concepts": ["Shakespeare"]},
                    {"title": "The Modernist Movement", "concepts": ["Modernism"]},
                    {"title": "Understanding Poetry", "concepts": ["Poetry Analysis"]}
                ]
            },
            {
                "name": "Computer Science", 
                "lectures": [(0, 14, 30), (2, 14, 30), (4, 14, 30)],  # Mon/Wed/Fri 2:30 PM
                "chapters": [
                    {"title": "Algorithm Design", "concepts": ["Algorithms"]},
                    {"title": "Data Structures Fundamentals", "concepts": ["Data Structures"]},
                    {"title": "Building for the Web", "concepts": ["Web Development"]}
                ]
            }
        ]

        classes = []
        
        for c_info in class_data:
            c_name = c_info["name"]
            join_code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
            
            # Term dates: Start 10 days ago, end in 90 days
            start_d = (datetime.now() - timedelta(days=10)).date()
            end_d = (datetime.now() + timedelta(days=90)).date()

            cls = Class(
                name=c_name, 
                teacher_id=teacher.id, 
                join_code=join_code,
                start_date=start_d,
                end_date=end_d
            )
            db.add(cls)
            db.flush()
            
            # Add Lectures from class-specific schedule
            for dow, hour, minute in c_info.get("lectures", [(0, 10, 0), (2, 10, 0), (4, 10, 0)]):
                lec = Lecture(
                    class_id=cls.id,
                    day_of_week=dow,
                    start_time=time(hour, minute),
                    duration_minutes=60
                )
                db.add(lec)
            db.flush()
            
            classes.append(cls)

            # Create chapters and concepts for this class
            cls_concepts = []
            for ch_order, ch_info in enumerate(c_info.get("chapters", [])):
                # Create concepts for this chapter
                chapter_concepts = []
                for concept_name in ch_info.get("concepts", []):
                    # Check if concept exists to avoid unique constraint error
                    concept = db.query(Concept).filter(Concept.name == concept_name).first()
                    if not concept:
                        concept = Concept(name=concept_name, description=f"Key concept of {c_name}")
                        db.add(concept)
                        db.flush()
                    chapter_concepts.append(concept)
                    cls_concepts.append(concept)
                
                # Create chapter
                chapter = Chapter(
                    title=ch_info["title"],
                    description=f"Chapter {ch_order + 1} of {c_name}",
                    class_id=cls.id,
                    order=ch_order
                )
                db.add(chapter)
                db.flush()
                
                # Link concepts to chapter
                chapter.concepts.extend(chapter_concepts)
                print(f"  Created chapter '{chapter.title}' with {len(chapter_concepts)} concept(s)")

            cls.related_concepts = cls_concepts
            print(f"Created class '{c_name}' with {len(c_info.get('chapters', []))} chapters")

        # 3. Students
        print("Creating Students...")
        students = []

        # Deon
        deon_email = "deon@school.com"
        deon_user = User(
            username="deon",
            email=deon_email,
            first_name="Deon",
            last_name="Student",
            hashed_password=get_password_hash("pw")
        )
        db.add(deon_user)
        db.flush()
        
        deon_student = Student(user_id=deon_user.id, name="Deon Student", email=deon_email)
        db.add(deon_student)
        db.flush()
        students.append(deon_student)

        # Realistic Mock Students
        mock_names = [
            "Sophia Chen", "Liam O'Connor", "Ava Patel", "Noah Jackson", 
            "Isabella Garcia", "Mason Kim", "Mia Thompson", "Ethan Wright", 
            "Harper Evans", "Lucas Nguyen", "Amelia Brooks", "Logan Davis", 
            "Charlotte Wilson", "Benjamin Lee", "Abigail Murphy", "William Carter", 
            "Emily White", "James Harris"
        ]

        for i, full_name in enumerate(mock_names):
            first, last = full_name.split(" ", 1)
            username = f"{first.lower()}_{last.lower().replace("'", "")}"
            email = f"{username}@school.com"
            
            u = User(
                username=username, 
                email=email, 
                first_name=first,
                last_name=last,
                hashed_password=get_password_hash("pw")
            )
            db.add(u)
            db.flush()
            
            s = Student(user_id=u.id, name=full_name, email=email)
            db.add(s)
            db.flush()
            students.append(s)

        # Enroll
        for s in students:
            for cls in classes:
                s.classes.append(cls)

        # 4. Assignments & Analytics
        print("Creating Assignments and Analytics Data...")
        
        for cls in classes:
            for j in range(1, 4):
                title = f"{cls.name} Assignment {j}"
                is_past = j < 3
                
                if is_past:
                    due_date = datetime.now() - timedelta(days=random.randint(5, 30))
                else:
                    due_date = datetime.now() + timedelta(days=random.randint(2, 14))

                assignment = Assignment(
                    title=title,
                    description=f"Assignment {j} details...",
                    due_at=due_date,
                    class_id=cls.id,
                    teacher_id=teacher.id,
                    structure_approved=True
                )
                db.add(assignment)
                db.flush()

                # Link Concepts
                concepts_for_assign = []
                if hasattr(cls, 'related_concepts') and cls.related_concepts:
                    # Pick 1-2 concepts
                    concepts_for_assign = random.sample(cls.related_concepts, k=min(2, len(cls.related_concepts)))
                    for lc in concepts_for_assign:
                        assignment.concepts.append(lc)
                
                # Grades
                for s in students:
                    if is_past:
                        # For each CONCEPT in the assignment
                        if concepts_for_assign:
                            for c in concepts_for_assign:
                                # Determine score. 
                                # Randomize weakness: 25% chance of < 0.6
                                if random.random() < 0.25:
                                    score = random.uniform(0.3, 0.59)
                                else:
                                    score = random.uniform(0.65, 0.98)

                                us = UnderstandingScore(
                                    student_id=s.user_id,
                                    assignment_id=assignment.id,
                                    concept_id=c.id, # Must be set for Weakness Grouping
                                    score=score,
                                    confidence=random.uniform(0.6, 1.0),
                                    source="assignment"
                                )
                                db.add(us)
                        else:
                            # Fallback if no concepts (shouldn't occur with seed logic)
                            us = UnderstandingScore(
                                student_id=s.user_id,
                                assignment_id=assignment.id,
                                score=random.uniform(0.6, 1.0),
                                confidence=0.8,
                                source="assignment"
                            )
                            db.add(us)

                    # Chat Logs
                    if random.random() > 0.4:
                        chat = ChatLog(
                            student_id=s.user_id,
                            assignment_id=assignment.id,
                            question=f"Question about {title}?",
                            created_at=due_date - timedelta(hours=24)
                        )
                        db.add(chat)
                    
                    # Events
                    if random.random() > 0.6:
                        evt_start = due_date - timedelta(days=2)
                        evt = CalendarEvent(
                            student_id=s.id,
                            class_id=cls.id,
                            title=f"Study {title}",
                            start_at=evt_start,
                            end_at=evt_start + timedelta(hours=1),
                            source="study_plan"
                        )
                        db.add(evt)

        db.commit()
        print("Success! Mock weakness data generated.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
