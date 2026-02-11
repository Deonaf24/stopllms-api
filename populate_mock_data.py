import random
from datetime import datetime, timedelta
from app.core.db import SessionLocal
from app.models.school import User, Teacher, Class, Student, Assignment, AssignmentQuestion, Concept, UnderstandingScore

def populate():
    db = SessionLocal()
    try:
        # 1. Get Teacher and Class (Targeting Algebra 101)
        class_id = 2 # Algebra 101
        class_ = db.query(Class).filter(Class.id == class_id).first()
        if not class_:
            print(f"Class {class_id} not found.")
            return

        teacher = class_.teacher
        if not teacher:
            print("Teacher not found for class.")
            return

        print(f"Adding assignments to Class: {class_.name} (ID: {class_.id}) for Teacher: {teacher.name}")
        
        # Reload students to ensure we have them
        students = db.query(Student).filter(Student.classes.any(id=class_.id)).all()
        if not students:
            print("No students in class.")
            return

        # 2. Define New Assignments
        new_assignments_data = [
            {"title": "Intro to Calculus", "concepts": ["Limits", "Derivatives"]},
            {"title": "Physics: Kinematics", "concepts": ["Velocity", "Acceleration"]},
            {"title": "World History: 19th Century", "concepts": ["Industrial Revolution", "Imperialism"]}
        ]

        for data in new_assignments_data:
            # Check if exists
            exists = db.query(Assignment).filter(Assignment.title == data["title"], Assignment.class_id == class_.id).first()
            if exists:
                print(f"Assignment {data['title']} already exists. Skipping.")
                continue

            # Create Assignment
            assignment = Assignment(
                title=data["title"],
                description=f"Mock assignment for {data['title']}",
                due_at=datetime.now() + timedelta(days=7),
                class_id=class_.id,
                teacher_id=teacher.id,
                structure_approved=True
            )
            db.add(assignment)
            db.flush()

            # Create Concepts and Questions
            concepts = []
            for c_name in data["concepts"]:
                concept = db.query(Concept).filter(Concept.name == c_name).first()
                if not concept:
                    concept = Concept(name=c_name, description="Mock concept")
                    db.add(concept)
                    db.flush()
                concepts.append(concept)
            
            assignment.concepts.extend(concepts)
            
            # Create Dummy Questions
            questions = []
            for i, concept in enumerate(concepts):
                question = AssignmentQuestion(
                    assignment_id=assignment.id,
                    prompt=f"Question about {concept.name}",
                    position=i+1
                )
                db.add(question)
                db.flush()
                question.concepts.append(concept)
                questions.append(question)

            # 3. Generate UnderstandingScores
            for student in students:
                for question in questions:
                    # Random score with some variance
                    base_score = random.uniform(0.3, 0.9)
                    if "Calculus" in data["title"]:
                        base_score -= 0.1 # Harder
                    if "History" in data["title"]:
                        base_score += 0.1 # Easier
                    
                    score_val = max(0.0, min(1.0, base_score + random.uniform(-0.1, 0.1)))
                    
                    q_concept = question.concepts[0]
                    
                    score = UnderstandingScore(
                        student_id=student.user_id,
                        assignment_id=assignment.id,
                        question_id=question.id,
                        concept_id=q_concept.id,
                        score=score_val,
                        confidence=0.8,
                        source="mock_script"
                    )
                    db.add(score)
                    
            print(f"Created assignment '{assignment.title}' with analytics data.")

        # 4. Create Chapters and Link Concepts
        print("Creating Chapters...")
        from app.models.school import Chapter  # Late import to ensure it's available

        chapters_data = [
            {
                "title": "Calculus Foundations",
                "description": "Introduction to limits and derivatives.",
                "concept_names": ["Limits", "Derivatives"]
            },
            {
                "title": "Physics Integration",
                "description": "Applying algebra to kinematics.",
                "concept_names": ["Velocity", "Acceleration"]
            },
            {
                "title": "Historical Context", 
                "description": "History related concepts.",
                "concept_names": ["Industrial Revolution", "Imperialism"]
            }
        ]

        for i, c_data in enumerate(chapters_data):
            # Check if chapter exists
            chapter = db.query(Chapter).filter(Chapter.title == c_data["title"], Chapter.class_id == class_.id).first()
            if not chapter:
                chapter = Chapter(
                    title=c_data["title"],
                    description=c_data["description"],
                    class_id=class_.id,
                    order=i
                )
                db.add(chapter)
                db.flush()
                print(f"Created chapter: {chapter.title}")
            
            # Link Concepts
            current_concepts = db.query(Concept).filter(Concept.name.in_(c_data["concept_names"])).all()
            
            # Re-fetch chapter to access relationships if it was just created (though flush handles ID, relationship loading might need object consistency)
            # existing_ids = {c.id for c in chapter.concepts} 
            # Simplified link logic:
            for conc in current_concepts:
                if conc not in chapter.concepts:
                    chapter.concepts.append(conc)
                    print(f"  Linked concept '{conc.name}' to '{chapter.title}'")

        db.commit()
        print("Successfully added mock assignments and chapters!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate()
