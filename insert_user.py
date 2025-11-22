from app.core.db import SessionLocal
from app.models.school import Teacher, Student, User

db = SessionLocal()

db.query(Teacher).delete()
db.query(Student).delete()
db.query(User).delete()

db.commit()
db.close()