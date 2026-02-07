import sys
import os
import random
from sqlalchemy.orm import Session
from sqlalchemy import select

# Add parent directory to path so we can import app modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.school import (
    Class, Student, Assignment, AssignmentQuestion, Concept, 
    UnderstandingScore, Chapter, Teacher
)

# Force psycopg 3 scheme
db_url = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_fake_analytics(db: Session, class_id: int):
    print(f"Generating analytics for Class ID: {class_id}")
    
    # 1. Fetch Class and Students
    class_obj = db.get(Class, class_id)
    if not class_obj:
        print("Class not found!")
        return

    students = class_obj.students
    if not students:
        print("No students in this class. Add students first.")
        # Try to find some students and add them?
        # For now, assume roster exists as per user context
        return

    print(f"Found {len(students)} students.")

    # 2. Ensure Concepts Exist
    concept_names = [
        "Linear Equations", "Quadratic Functions", "Polynomials", 
        "Rational Expressions", "Exponential Functions", "Logarithms",
        "Trigonometry", "Geometry Basics", "Probability", "Statistics"
    ]
    
    concepts = []
    for name in concept_names:
        concept = db.query(Concept).filter(Concept.name == name).first()
        if not concept:
            concept = Concept(name=name, description=f"Basic understanding of {name}")
            db.add(concept)
            db.commit()
            db.refresh(concept)
        concepts.append(concept)
    
    # 3. Ensure Chapters Exist (and contain concepts)
    chapter_titles = ["Algebra I", "Algebra II", "Geometry", "Pre-Calculus"]
    chapters = []
    for i, title in enumerate(chapter_titles):
        chapter = db.query(Chapter).filter(Chapter.class_id == class_id, Chapter.title == title).first()
        if not chapter:
            chapter = Chapter(title=title, class_id=class_id, order=i)
            db.add(chapter)
            db.commit()
            db.refresh(chapter)
        
        # Link random concepts to chapter if empty
        if not chapter.concepts:
            chapter.concepts = random.sample(concepts, k=random.randint(2, 4))
            db.commit()
        
        chapters.append(chapter)

    # 4. Ensure Assignments Exist (we want at least 5 for good data)
    current_count = len(class_obj.assignments)
    if current_count < 5:
        print(f"Only {current_count} assignments found. Creating {5 - current_count} more...")
        for i in range(current_count, 5):
            assignment = Assignment(
                title=f"Mock Assignment {i+1} - {chapters[i % len(chapters)].title}",
                description=f"Practice for {chapters[i % len(chapters)].title}",
                class_id=class_id,
                teacher_id=class_obj.teacher_id,
                due_at=None
            )
            # Link to chapter and concepts
            chapter = chapters[i % len(chapters)]
            assignment.chapters.append(chapter)
            
            # Ensure chapter has concepts
            if not chapter.concepts:
                 chapter.concepts = random.sample(concepts, k=random.randint(2, 4))
            
            assignment.concepts = chapter.concepts
            
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            
            # Create dummy questions
            for j in range(5): # 5 questions per assignment
                question = AssignmentQuestion(
                    assignment_id=assignment.id,
                    prompt=f"Question {j+1} for {assignment.title}",
                    position=j
                )
                db.add(question)
                # Link question to a concept
                if assignment.concepts:
                    question.concepts.append(random.choice(assignment.concepts))
            db.commit()
    
    # Reload assignments
    db.expire(class_obj)
    db.refresh(class_obj)
    assignments = class_obj.assignments
    print(f"Found {len(assignments)} assignments.")

    # 5. Generate Understanding Scores
    print("Generating scores...")
    
    for student in students:
        print(f"  Processing {student.name}...")
        
        # Determine student "archetype" (Advanced, Average, Struggling)
        archetype = random.choice(["advanced", "average", "struggling"])
        # Add some randomness to archetype consistency
        base_score = 0.85 if archetype == "advanced" else 0.6 if archetype == "average" else 0.4
        
        for assignment in assignments:
            # Randomly decide if student did this assignment (90% chance now)
            if random.random() < 0.1:
                continue
            
            # Ensure assignment has questions, if not create them (retroactive fix for existing empty assignments)
            if not assignment.questions:
                 # Link concepts if missing
                 if not assignment.concepts:
                     # Pick random concepts
                     assignment.concepts = random.sample(concepts, k=2)
                     db.commit()

                 for j in range(3):
                    q = AssignmentQuestion(assignment_id=assignment.id, prompt="Auto-gen question", position=j)
                    db.add(q)
                    q.concepts.append(random.choice(assignment.concepts))
                 db.commit()

            # For each question/concept in assignment
            for question in assignment.questions:
                # Calculate score based on archetype + variance
                score_val = min(1.0, max(0.0, random.gauss(base_score, 0.2)))
                
                # Concept linking
                concept = question.concepts[0] if question.concepts else None
                concept_id = concept.id if concept else None
                
                if not concept_id and assignment.concepts:
                     # Fallback: link question to a random assignment concept if missing
                     concept = random.choice(assignment.concepts)
                     question.concepts.append(concept)
                     concept_id = concept.id
                     db.commit()
                
                # Check if score exists
                existing = db.query(UnderstandingScore).filter(
                    UnderstandingScore.student_id == student.user_id, # Link via User ID!
                    UnderstandingScore.assignment_id == assignment.id,
                    UnderstandingScore.question_id == question.id
                ).first()

                if not existing:
                    us = UnderstandingScore(
                        student_id=student.user_id,
                        assignment_id=assignment.id,
                        question_id=question.id,
                        concept_id=concept_id,
                        score=score_val,
                        confidence=random.uniform(0.5, 1.0),
                        source="mock_script"
                    )
                    db.add(us)
                else:
                    existing.score = score_val
                    existing.concept_id = concept_id # Ensure concept is linked even on update
            
    db.commit()
    print("Done! Analytics generated.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Find the first class with students, or just the first class
        # Ideally, we find the "Socratica" class user is viewing.
        # Let's list classes and ask or pick one.
        classes = db.query(Class).all()
        if not classes:
            print("No classes found in DB.")
        else:
            for c in classes:
                print(f"Class: {c.id} - {c.name} ({len(c.students)} students)")
            
            # Pick 'test' class if exists, else first class with students
            target_class = next((c for c in classes if c.name.lower() == "test"), None)
            if not target_class:
                target_class = next((c for c in classes if c.students), classes[0])
            
            create_fake_analytics(db, target_class.id)
            
    finally:
        db.close()
