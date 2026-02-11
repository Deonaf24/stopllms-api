
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import sys
import os
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.db import SessionLocal
from app.models.school import User, Teacher, Class, Student
from app.core.security import get_password_hash # Import hashing function
from populate_mock_data import populate

def restore():
    db = SessionLocal()
    print("Restoring Mock Data...")

    try:
        # 1. Cleanup
        # We delete manually to avoid FK issues, or use cascade
        print("Cleaning up old data...")
        db.query(Class).delete()
        db.query(Teacher).delete()
        db.query(Student).delete()
        db.query(User).delete()
        db.commit()

        # 2. Create Users
        print("Creating Users...")
        # Teacher
        teacher_user = User(
            username="mr_socratic", 
            email="teacher@socratica.com", 
            hashed_password=get_password_hash("pw") 
        )
        db.add(teacher_user)
        db.flush() # get ID

        teacher = Teacher(
            name="Mr. Socratic",
            email="teacher@socratica.com",
            user_account=teacher_user
        )
        db.add(teacher)
        
        # Student (Deon)
        deon_user = User(
            username="deon", 
            email="deon@test.com", 
            hashed_password=get_password_hash("pw") 
        )
        db.add(deon_user)
        db.flush()

        deon_student = Student(
            name="Deon",
            email="deon@test.com",
            user_account=deon_user
        )
        db.add(deon_student)
        
        # Create 19 more mock students
        other_students = []
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
                       "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
        
        # We use a subset or repeat if needed, but 19 is fine.
        for i in range(19):
            name = first_names[i] if i < len(first_names) else f"Student_{i}"
            username = f"{name.lower()}_{i}"
            email = f"{username}@test.com"
            
            s_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash("pw")
            )
            db.add(s_user)
            db.flush()
            
            student = Student(
                name=name,
                email=email,
                user_account=s_user
            )
            db.add(student)
            other_students.append(student)

        db.commit() # Commit to save IDs

        # 3. Create Class (ID 2 to match populate script expectation)
        print("Creating Class...")
        # Force ID 2 if possible, or just create and let populate find it if we adjust populate.
        # But populate hardcodes `class_id = 2`.
        # We can try to force ID by passing it, but autoincrement might ignore or conflict.
        # Safest is to just create it and update populate.py or use SQL injection.
        # OR: Just create and hope ID 1 or 2.
        # Actually, let's just create it. If `populate_mock_data.py` fails on ID 2, 
        # I will patch `populate_mock_data.py` to find the class by name.
        
        algebra_class = Class(
            id=2, # Trying to force ID for compatibility
            name="Algebra 101",
            join_code="ALG101",
            teacher_id=teacher.id
        )
        algebra_class.students.append(deon_student)
        for s in other_students:
            algebra_class.students.append(s)
            
        db.add(algebra_class)
        
        # Also need sequence update if we force ID? 
        # Usually SQLAlchemy handles this if we don't commit immediately?
        # Postgres might complain about sequence out of sync later, but for mock data fine.
        
        try:
             db.commit()
        except Exception as e:
            print(f"Could not force ID 2: {e}. Trying without ID...")
            db.rollback()
            algebra_class = Class(
                name="Algebra 101",
                join_code="ALG101",
                teacher_id=teacher.id
            )
            algebra_class.students.append(deon_student)
            for s in other_students:
                algebra_class.students.append(s)
                
            db.add(algebra_class)
            db.commit()
            print(f"Created Class with ID {algebra_class.id} (Populate might fail if it expects 2)")

        print("Users and Class restored.")
        
    except Exception as e:
        print(f"Error restoring base data: {e}")
        db.rollback()
        return
    finally:
        db.close()

    # 4. Run Populate
    print("Running populate_mock_data...")
    try:
        populate()
    except Exception as e:
        print(f"Populate failed: {e}")

if __name__ == "__main__":
    restore()
