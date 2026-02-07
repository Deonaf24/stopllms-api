from pydantic import BaseModel
from typing import List

class LiveQueryRequest(BaseModel):
    concept_ids: List[int]
    question_type: List[str] = ["multiple_choice"]
    time_limit: int = 15

class LiveQuestion(BaseModel):
    id: int
    text: str
    question_type: str
    options: List[str] | None = None
    order: int

    class Config:
        from_attributes = True

class LiveSession(BaseModel):
    id: int
    class_id: int
    status: str
    current_question_index: int
    questions: List[LiveQuestion]

    class Config:
        from_attributes = True

class LiveQueryResponse(BaseModel):
    session: LiveSession
    context_summary: str

class LiveAnswerRequest(BaseModel):
    student_id: int
    answer: str
    time_spent_seconds: int = 0

class LiveAnswerResponse(BaseModel):
    status: str
    is_correct: bool | None = None
    correct_answer: str | None = None

class LiveStatsResponse(BaseModel):
    question_id: int | None
    total_responses: int
    distribution: dict[str, int]

class LiveDashboardStats(BaseModel):
    session_id: int
    total_students: int
    questions: list[LiveStatsResponse]

class LiveResponseGrading(BaseModel):
    is_correct: bool

class LiveResponseRead(BaseModel):
    id: int
    question_id: int
    question_text: str | None = None
    student_id: int
    answer: str
    is_correct: bool | None = None
    
    class Config:
        from_attributes = True


# Session History Schemas
from datetime import datetime

class LiveSessionSummary(BaseModel):
    """Summary of a live session for the history list"""
    id: int
    class_id: int
    status: str
    created_at: datetime
    ended_at: datetime | None = None
    question_count: int
    response_count: int
    participant_count: int

    class Config:
        from_attributes = True


class StudentQuestionResult(BaseModel):
    """A student's answer for a single question"""
    question_id: int
    question_text: str
    question_type: str
    answer: str | None = None
    is_correct: bool | None = None
    time_spent_seconds: int = 0


class StudentSessionResult(BaseModel):
    """A student's complete results for a session"""
    student_id: int
    total_correct: int
    total_answered: int
    responses: list[StudentQuestionResult]


class LiveDetailedStats(BaseModel):
    """Detailed analytics for a past session"""
    session_id: int
    class_id: int
    created_at: datetime
    ended_at: datetime | None = None
    questions: list[LiveQuestion]
    student_results: list[StudentSessionResult]
    overall_accuracy: float  # percentage
