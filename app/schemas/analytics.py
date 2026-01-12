from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptBase(BaseModel):
    name: str
    description: Optional[str] = None


class ConceptCreate(ConceptBase):
    pass


class ConceptRead(ConceptBase, TimestampModel):
    id: int


class AssignmentQuestionBase(BaseModel):
    prompt: str
    position: Optional[int] = None


class AssignmentQuestionCreate(AssignmentQuestionBase):
    assignment_id: int


class AssignmentQuestionRead(AssignmentQuestionBase, TimestampModel):
    id: int
    assignment_id: int
    concept_ids: List[int] = Field(default_factory=list)


class UnderstandingScoreBase(BaseModel):
    student_id: int
    assignment_id: int
    question_id: Optional[int] = None
    concept_id: Optional[int] = None
    score: float
    confidence: Optional[float] = None
    source: Optional[str] = None


class UnderstandingScoreCreate(UnderstandingScoreBase):
    pass


class UnderstandingScoreRead(UnderstandingScoreBase, TimestampModel):
    id: int


class AssignmentConceptLink(BaseModel):
    concept_id: int


class QuestionConceptLink(BaseModel):
    question_id: int
    concept_id: int


class ConceptPayload(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None


class AssignmentQuestionPayload(BaseModel):
    id: Optional[int] = None
    prompt: str
    position: Optional[int] = None
    concept_ids: List[int] = Field(default_factory=list)


class AssignmentStructureReview(BaseModel):
    assignment_id: int
    concepts: List[ConceptPayload] = Field(default_factory=list)
    questions: List[AssignmentQuestionPayload] = Field(default_factory=list)
    question_concepts: List[QuestionConceptLink] = Field(default_factory=list)
    assignment_concepts: List[AssignmentConceptLink] = Field(default_factory=list)


class AssignmentStructureReviewRead(AssignmentStructureReview):
    structure_approved: bool = False


class AssignmentScoreSummary(BaseModel):
    assignment_id: int
    assignment_title: str
    average_score: float

    @classmethod
    def from_row(cls, row) -> "AssignmentScoreSummary | None":
        if not row:
            return None
        return cls(
            assignment_id=row.assignment_id,
            assignment_title=row.assignment_title,
            average_score=float(row.avg_score)
        )


class ConceptScoreSummary(BaseModel):
    concept_id: int
    concept_name: str
    average_score: float

    @classmethod
    def from_row(cls, row) -> "ConceptScoreSummary | None":
        if not row:
            return None
        return cls(
            concept_id=row.concept_id,
            concept_name=row.concept_name,
            average_score=float(row.avg_score),
        )


class QuestionScoreSummary(BaseModel):
    question_id: int
    question_prompt: str
    average_score: float

    @classmethod
    def from_row(cls, row) -> "QuestionScoreSummary | None":
        if not row:
            return None
        return cls(
            question_id=row.question_id,
            question_prompt=row.question_prompt,
            average_score=float(row.avg_score),
        )


class StudentScoreSummary(BaseModel):
    student_id: int
    student_name: str
    average_score: float


class StudentAnalyticsRead(BaseModel):
    student_id: int
    questions_asked: int
    easiest_assignment: AssignmentScoreSummary | None
    hardest_assignment: AssignmentScoreSummary | None
    most_understood_concept: ConceptScoreSummary | None
    least_understood_concept: ConceptScoreSummary | None



class WeaknessGroup(BaseModel):
    concept_id: int
    concept_name: str
    students: list[StudentScoreSummary] = []
    average_score: float


class AssignmentAnalyticsRead(BaseModel):
    assignment_id: int
    most_understood_concept: ConceptScoreSummary | None
    least_understood_concept: ConceptScoreSummary | None
    most_understood_question: QuestionScoreSummary | None
    least_understood_question: QuestionScoreSummary | None
    student_rankings: list[StudentScoreSummary] = []
    weakness_groups: list[WeaknessGroup] = []


class ClassAnalyticsRead(BaseModel):
    class_id: int
    most_understood_assignment: AssignmentScoreSummary | None
    least_understood_assignment: AssignmentScoreSummary | None
    student_rankings: list[StudentScoreSummary]
    weakness_groups: list[WeaknessGroup] = []
