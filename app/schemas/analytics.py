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
