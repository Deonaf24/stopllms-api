from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any, Iterable

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.school import Assignment, AssignmentQuestion, Concept
from app.schemas.analytics import (
    AssignmentConceptLink,
    AssignmentQuestionPayload,
    AssignmentStructureReviewRead,
    ConceptPayload,
    QuestionConceptLink,
)
from app.services.llm import ollama_generate


class AssignmentAnalysisError(Exception):
    """Raised when assignment analysis fails."""


def _build_assignment_extraction_prompt(text: str) -> str:
    return (
        "You are an assistant that extracts assignment structure.\n"
        "Return ONLY valid JSON matching this schema:\n"
        "{\n"
        '  "concepts": [\n'
        '    {"id": "C1", "name": "Concept name", "description": "optional"}\n'
        "  ],\n"
        '  "questions": [\n'
        '    {"id": "Q1", "prompt": "question text", "position": 1}\n'
        "  ],\n"
        '  "question_concepts": [\n'
        '    {"question_id": "Q1", "concept_id": "C1"}\n'
        "  ],\n"
        '  "assignment_concepts": [\n'
        '    {"concept_id": "C1"}\n'
        "  ]\n"
        "}\n"
        "If a field is unknown, return an empty list. Do not add extra keys.\n"
        "Assignment content:\n"
        f"{text}\n"
    )


def _extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_from_bytes(data: bytes, filename: str | None, mime_type: str | None) -> str:
    lowered_name = (filename or "").lower()
    if (mime_type and "pdf" in mime_type) or lowered_name.endswith(".pdf"):
        return _extract_text_from_pdf(data)
    return data.decode("utf-8", errors="ignore")


def _parse_llm_json(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise AssignmentAnalysisError("Failed to parse JSON from model output")
        return json.loads(match.group(0))


def _normalize_list(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _link_assignment_concepts(
    assignment: Assignment,
    concepts: dict[str, Concept],
    assignment_concept_payloads: Iterable[dict[str, Any]],
) -> list[int]:
    if assignment_concept_payloads:
        concept_ids = [
            concepts[payload.get("concept_id")].id
            for payload in assignment_concept_payloads
            if payload.get("concept_id") in concepts
        ]
        assignment.concepts = [concept for concept in concepts.values() if concept.id in concept_ids]
        return concept_ids
    assignment.concepts = list(concepts.values())
    return [concept.id for concept in assignment.concepts]


async def analyze_assignment_structure(
    db: Session, assignment: Assignment
) -> AssignmentStructureReviewRead:
    from app.services.storage import StorageError, get_storage_service

    storage = get_storage_service()
    if not assignment.files:
        raise AssignmentAnalysisError("Assignment has no files to analyze")

    extracted_texts = []
    for file in assignment.files:
        try:
            data = await storage.open_file(file.path)
        except StorageError as exc:
            raise AssignmentAnalysisError("Unable to read assignment file") from exc
        extracted_texts.append(_extract_text_from_bytes(data, file.filename, file.mime_type))

    combined_text = "\n\n".join(text for text in extracted_texts if text.strip())
    if not combined_text.strip():
        raise AssignmentAnalysisError("Assignment content was empty after extraction")

    prompt = _build_assignment_extraction_prompt(combined_text)
    raw = ollama_generate(prompt)
    payload = _parse_llm_json(raw)

    concept_payloads = _normalize_list(payload.get("concepts"))
    question_payloads = _normalize_list(payload.get("questions"))
    question_concepts = _normalize_list(payload.get("question_concepts"))
    assignment_concepts = _normalize_list(payload.get("assignment_concepts"))

    assignment.questions.clear()
    assignment.concepts.clear()
    db.flush()

    concept_map: dict[str, Concept] = {}
    concept_responses: list[ConceptPayload] = []
    for concept in concept_payloads:
        concept_key = concept.get("id") or concept.get("name")
        name = concept.get("name")
        if not name or not concept_key:
            continue
        existing = db.query(Concept).filter(Concept.name == name).one_or_none()
        if existing:
            if concept.get("description") and existing.description != concept.get("description"):
                existing.description = concept.get("description")
            concept_obj = existing
        else:
            concept_obj = Concept(name=name, description=concept.get("description"))
            db.add(concept_obj)
        db.flush()
        concept_map[str(concept_key)] = concept_obj
        concept_responses.append(
            ConceptPayload(id=concept_obj.id, name=concept_obj.name, description=concept_obj.description)
        )

    questions: dict[str, AssignmentQuestion] = {}
    question_responses: list[AssignmentQuestionPayload] = []
    for question in question_payloads:
        question_key = question.get("id")
        prompt_text = question.get("prompt")
        if not question_key or not prompt_text:
            continue
        question_obj = AssignmentQuestion(
            assignment_id=assignment.id,
            prompt=prompt_text,
            position=question.get("position"),
        )
        db.add(question_obj)
        db.flush()
        questions[str(question_key)] = question_obj
        question_responses.append(
            AssignmentQuestionPayload(
                id=question_obj.id,
                prompt=question_obj.prompt,
                position=question_obj.position,
            )
        )

    question_concept_links: list[QuestionConceptLink] = []
    for link in question_concepts:
        q_key = link.get("question_id")
        c_key = link.get("concept_id")
        if not q_key or not c_key:
            continue
        question_obj = questions.get(str(q_key))
        concept_obj = concept_map.get(str(c_key))
        if not question_obj or not concept_obj:
            continue
        question_obj.concepts.append(concept_obj)
        question_concept_links.append(
            QuestionConceptLink(question_id=question_obj.id, concept_id=concept_obj.id)
        )

    assignment_concept_links = [
        AssignmentConceptLink(concept_id=concept_id)
        for concept_id in _link_assignment_concepts(assignment, concept_map, assignment_concepts)
    ]

    for response in question_responses:
        response.concept_ids = [
            link.concept_id for link in question_concept_links if link.question_id == response.id
        ]

    assignment.structure_approved = False
    db.commit()
    db.refresh(assignment)

    return AssignmentStructureReviewRead(
        assignment_id=assignment.id,
        concepts=concept_responses,
        questions=question_responses,
        question_concepts=question_concept_links,
        assignment_concepts=assignment_concept_links,
        structure_approved=assignment.structure_approved,
    )
