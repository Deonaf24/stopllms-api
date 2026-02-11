from __future__ import annotations

from datetime import datetime, date, time

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
    JSON,
    Date,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class_students = Table(
    "class_students",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
)

assignment_concepts = Table(
    "assignment_concepts",
    Base.metadata,
    Column("assignment_id", ForeignKey("assignments.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)

question_concepts = Table(
    "question_concepts",
    Base.metadata,
    Column("question_id", ForeignKey("assignment_questions.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)

material_concepts = Table(
    "material_concepts",
    Base.metadata,
    Column("material_id", ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)

chapter_concepts = Table(
    "chapter_concepts",
    Base.metadata,
    Column("chapter_id", ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)

chapter_assignments = Table(
    "chapter_assignments",
    Base.metadata,
    Column("chapter_id", ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True),
    Column("assignment_id", ForeignKey("assignments.id", ondelete="CASCADE"), primary_key=True),
)

chapter_materials = Table(
    "chapter_materials",
    Base.metadata,
    Column("chapter_id", ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True),
    Column("material_id", ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class User(TimestampMixin, Base):
    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Authentication Fields (Unique and required for login)
    username: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # SECURITY FIELD: Stores the hashed password
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # State/Permissions
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Google Integration
    google_refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationship for Teacher
    teacher_link: Mapped[Teacher] = relationship(
        "Teacher", 
        back_populates="user_account",
        uselist=False,
        cascade="all, delete",
    )

    # Relationship for Student
    student_link: Mapped[Student] = relationship(
        "Student", 
        back_populates="user_account",
        uselist=False,
        cascade="all, delete",
    )

    @property
    def is_teacher(self) -> bool:
        # Falls back gently to no-profile
        try:
            return self.teacher_link is not None
        except:
            return False

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    user_account: Mapped[User] = relationship("User", back_populates="teacher_link")

    classes: Mapped[list[Class]] = relationship("Class", back_populates="teacher")
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="teacher"
    )
    materials: Mapped[list[Material]] = relationship(
        "Material", back_populates="teacher"
    )

    def __repr__(self) -> str:
        return f"<Teacher id={self.id} email={self.email!r}>"


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    user_account: Mapped[User] = relationship("User", back_populates="student_link")

    classes: Mapped[list[Class]] = relationship(
        secondary=class_students, back_populates="students"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} email={self.email!r}>"


class Class(TimestampMixin, Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    join_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Google Integration
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_google_synced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    teacher: Mapped[Teacher | None] = relationship("Teacher", back_populates="classes")
    students: Mapped[list[Student]] = relationship(
        secondary=class_students, back_populates="classes"
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="class_", cascade="all, delete-orphan"
    )
    announcements: Mapped[list[Announcement]] = relationship(
        "Announcement", back_populates="class_", cascade="all, delete-orphan"
    )
    polls: Mapped[list[Poll]] = relationship(
        "Poll", back_populates="class_", cascade="all, delete-orphan"
    )
    materials: Mapped[list[Material]] = relationship(
        "Material", back_populates="class_", cascade="all, delete-orphan"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter", back_populates="class_", cascade="all, delete-orphan"
    )
    live_sessions: Mapped[list[LiveSession]] = relationship(
        "LiveSession", back_populates="class_", cascade="all, delete-orphan"
    )
    lectures: Mapped[list[Lecture]] = relationship(
        "Lecture", back_populates="class_", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Class id={self.id} name={self.name!r}>"


class Assignment(TimestampMixin, Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    structure_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Google Integration
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    google_link: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )

    class_: Mapped[Class] = relationship("Class", back_populates="assignments")
    teacher: Mapped[Teacher | None] = relationship("Teacher", back_populates="assignments")
    files: Mapped[list[File]] = relationship(
        "File", back_populates="assignment", cascade="all, delete-orphan"
    )
    concepts: Mapped[list[Concept]] = relationship(
        "Concept", secondary=assignment_concepts, back_populates="assignments"
    )
    questions: Mapped[list[AssignmentQuestion]] = relationship(
        "AssignmentQuestion", back_populates="assignment", cascade="all, delete-orphan"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter", secondary=chapter_assignments, back_populates="assignments"
    )

    def __repr__(self) -> str:
        return f"<Assignment id={self.id} title={self.title!r}>"


class StudentAssignment(TimestampMixin, Base):
    __tablename__ = "student_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    google_submission_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50)) # CREATED, TURNED_IN, RETURNED, RECLAIMED_BY_STUDENT
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)

    student: Mapped[User] = relationship("User")
    assignment: Mapped[Assignment] = relationship("Assignment")

    def __repr__(self) -> str:
        return f"<StudentAssignment student={self.student_id} assignment={self.assignment_id} status={self.status}>"


class Material(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    class_: Mapped[Class] = relationship("Class", back_populates="materials")
    teacher: Mapped[Teacher] = relationship("Teacher", back_populates="materials")
    files: Mapped[list[File]] = relationship(
        "File", back_populates="material", cascade="all, delete-orphan"
    )
    concepts: Mapped[list[Concept]] = relationship(
        "Concept", secondary=material_concepts, back_populates="materials"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter", secondary=chapter_materials, back_populates="materials"
    )

    def __repr__(self) -> str:
        return f"<Material id={self.id} title={self.title!r}>"


class File(TimestampMixin, Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True
    )
    announcement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=True
    )
    poll_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=True
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=True
    )

    assignment: Mapped[Assignment | None] = relationship("Assignment", back_populates="files")
    announcement: Mapped[Announcement | None] = relationship("Announcement", back_populates="files")
    poll: Mapped[Poll | None] = relationship("Poll", back_populates="files")
    material: Mapped[Material | None] = relationship("Material", back_populates="files")

    def __repr__(self) -> str:
        return f"<File id={self.id} filename={self.filename!r}>"


class ChatLog(TimestampMixin, Base):
    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assignment_questions.id", ondelete="SET NULL"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)

    student: Mapped[User] = relationship("User")
    assignment: Mapped[Assignment] = relationship("Assignment")

    def __repr__(self) -> str:
        return f"<ChatLog id={self.id} student={self.student_id}>"


class Concept(TimestampMixin, Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", secondary=assignment_concepts, back_populates="concepts"
    )
    questions: Mapped[list[AssignmentQuestion]] = relationship(
        "AssignmentQuestion", secondary=question_concepts, back_populates="concepts"
    )
    materials: Mapped[list[Material]] = relationship(
        "Material", secondary=material_concepts, back_populates="concepts"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter", secondary=chapter_concepts, back_populates="concepts"
    )

    def __repr__(self) -> str:
        return f"<Concept id={self.id} name={self.name!r}>"


class AssignmentQuestion(TimestampMixin, Base):
    __tablename__ = "assignment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer)

    assignment: Mapped[Assignment] = relationship("Assignment", back_populates="questions")
    concepts: Mapped[list[Concept]] = relationship(
        "Concept", secondary=question_concepts, back_populates="questions"
    )

    def __repr__(self) -> str:
        return f"<AssignmentQuestion id={self.id} assignment={self.assignment_id}>"


class UnderstandingScore(TimestampMixin, Base):
    __tablename__ = "understanding_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assignment_questions.id", ondelete="SET NULL"), nullable=True
    )
    concept_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(64))

    student: Mapped[User] = relationship("User")
    assignment: Mapped[Assignment] = relationship("Assignment")
    question: Mapped[AssignmentQuestion | None] = relationship("AssignmentQuestion")
    concept: Mapped[Concept | None] = relationship("Concept")

    def __repr__(self) -> str:
        return f"<UnderstandingScore id={self.id} student={self.student_id}>"


class Announcement(TimestampMixin, Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False) # Acting as description/body
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    class_: Mapped[Class] = relationship("Class", back_populates="announcements")
    author: Mapped[Teacher] = relationship("Teacher")
    files: Mapped[list[File]] = relationship(
        "File", back_populates="announcement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Announcement id={self.id}>"


class Poll(TimestampMixin, Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    class_: Mapped[Class] = relationship("Class", back_populates="polls")
    author: Mapped[Teacher] = relationship("Teacher")
    options: Mapped[list[PollOption]] = relationship(
        "PollOption", back_populates="poll", cascade="all, delete-orphan"
    )
    files: Mapped[list[File]] = relationship(
        "File", back_populates="poll", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Poll id={self.id} question={self.question!r}>"


class PollOption(Base):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    poll_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    
    poll: Mapped[Poll] = relationship("Poll", back_populates="options")
    votes: Mapped[list[PollVote]] = relationship(
        "PollVote", back_populates="option", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PollOption id={self.id} text={self.text!r}>"


class PollVote(TimestampMixin, Base):
    __tablename__ = "poll_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    poll_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    option_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )

    poll: Mapped[Poll] = relationship("Poll")
    option: Mapped[PollOption] = relationship("PollOption", back_populates="votes")
    student: Mapped[Student] = relationship("Student")

    def __repr__(self) -> str:
        return f"<PollVote id={self.id} student={self.student_id}>"


class Chapter(TimestampMixin, Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    class_: Mapped[Class] = relationship("Class", back_populates="chapters")
    
    concepts: Mapped[list[Concept]] = relationship(
        "Concept", secondary=chapter_concepts, back_populates="chapters"
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", secondary=chapter_assignments, back_populates="chapters"
    )
    materials: Mapped[list[Material]] = relationship(
        "Material", secondary=chapter_materials, back_populates="chapters"
    )

    def __repr__(self) -> str:
        return f"<Chapter id={self.id} title={self.title!r}>"


class LiveSession(TimestampMixin, Base):
    __tablename__ = "live_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False) # active, ended
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    concept_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)

    class_: Mapped[Class] = relationship("Class", back_populates="live_sessions")
    
    questions: Mapped[list[LiveQuestion]] = relationship(
        "LiveQuestion", back_populates="session", cascade="all, delete-orphan", order_by="LiveQuestion.order"
    )

    def __repr__(self) -> str:
        return f"<LiveSession id={self.id} class={self.class_id}>"


class LiveQuestion(Base):
    __tablename__ = "live_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False) # multiple_choice, true_false, short_answer
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True) # json string or raw text
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped[LiveSession] = relationship("LiveSession", back_populates="questions")
    responses: Mapped[list[LiveResponse]] = relationship(
        "LiveResponse", back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LiveQuestion id={self.id} type={self.question_type}>"


class LiveResponse(TimestampMixin, Base):
    __tablename__ = "live_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("live_questions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[LiveQuestion] = relationship("LiveQuestion", back_populates="responses")
    student: Mapped[Student] = relationship("Student")

    def __repr__(self) -> str:
        return f"<LiveResponse id={self.id} student={self.student_id} correct={self.is_correct}>"


class Lecture(Base):
    __tablename__ = "lectures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False) # 0=Monday, 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    class_: Mapped[Class] = relationship("Class", back_populates="lectures")

    def __repr__(self) -> str:
        return f"<Lecture id={self.id} class={self.class_id} day={self.day_of_week}>"
