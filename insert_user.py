import sys
import os
# Ensure the app package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.db import SessionLocal
from app.models.school import User # Import the User model from where you put it

# This is the HASHED password you provided
TEST_HASHED_PASSWORD = "$2b$12$D.rf6mRn01c/3SbGddsHoet2OPN46HlkyjPnnYwaLtsVEQCT2tiAu"

def insert_initial_user():
    with SessionLocal() as db:
        # 1. Check if the user already exists
        existing_user = db.query(User).filter(User.username == "deon").first()
        if existing_user:
            print("User 'deon' already exists. Skipping insertion.")
            return

        # 2. Create the User object
        new_user = User(
            username="deon",
            email="deon.aftahi@gmail.com",
            hashed_password=TEST_HASHED_PASSWORD,
            disabled=False
        )

        # 3. Add to session and commit to DB
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Successfully inserted new user: ID {new_user.id}, Username: {new_user.username}")

if __name__ == "__main__":
    insert_initial_user()