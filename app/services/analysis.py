from __future__ import annotations

import json
import logging
import re
from io import BytesIO
from typing import Any, Iterable

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.school import Assignment, AssignmentQuestion, ChatLog, Concept, UnderstandingScore
from app.schemas.analytics import (
    AssignmentConceptLink,
    AssignmentQuestionPayload,
    AssignmentStructureReview,
    AssignmentStructureReviewRead,
    ConceptPayload,
    QuestionConceptLink,
)
from app.services.llm import generate_text
from app.services.prompts import build_assignment_extraction_prompt, build_assignment_scoring_prompt


class AssignmentAnalysisError(Exception):
    """Raised when assignment analysis fails."""

logger = logging.getLogger(__name__)


def _extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_from_bytes(data: bytes, filename: str | None, mime_type: str | None) -> str:
    lowered_name = (filename or "").lower()
    if (mime_type and "pdf" in mime_type) or lowered_name.endswith(".pdf"):
        return _extract_text_from_pdf(data)
    
    # We cannot extract text from images without OCR dependencies
    if (mime_type and "image" in mime_type) or lowered_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        logger.warning("Skipping image file %s as OCR is not available", filename)
        return ""

    return data.decode("utf-8", errors="ignore")


def _parse_llm_json(raw: str) -> dict[str, Any]:
    # Try to clean markdown code blocks first
    if "```" in raw:
        match = re.search(r"```(?:json)?(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
            
    # Fix invalid escape sequences (common in Latex/Math content from LLMs)
    # Replaces backslash with double-backslash unless it's a valid JSON escape char
    raw = re.sub(r'\\(?![/u"bfnrt\\])', r'\\\\', raw)
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON Direct Parse Failed: {e}")
        # Fallback regex for {}
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            logger.warning("Failed to parse JSON from model output")
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e2:
            print(f"DEBUG: JSON Regex Parse Failed: {e2}")
            print(f"DEBUG: Raw Tail (last 100 chars): {raw[-100:]}")
            logger.warning("Failed to parse JSON from extracted payload")
            return {}


def _normalize_list(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_score_entries(value: Any) -> list[dict[str, Any]]:
    entries = _normalize_list(value)
    normalized = []
    for entry in entries:
        if "student_id" not in entry or "score" not in entry:
            continue
        try:
            score_value = float(entry["score"])
        except (TypeError, ValueError):
            continue
        if not 0 <= score_value <= 1:
            continue
        entry["score"] = score_value
        normalized.append(entry)
    return normalized


def _validate_extraction_payload(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return {"concepts": [], "questions": [], "question_concepts": [], "assignment_concepts": []}
    return {
        "concepts": _normalize_list(payload.get("concepts")),
        "questions": _normalize_list(payload.get("questions")),
        "question_concepts": _normalize_list(payload.get("question_concepts")),
        "assignment_concepts": _normalize_list(payload.get("assignment_concepts")),
    }


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

    from app.core.config import settings

    extracted_texts = []
    file_payloads = []
    for file in assignment.files:
        try:
            data = await storage.open_file(file.path)
            extracted_texts.append(_extract_text_from_bytes(data, file.filename, file.mime_type))
            if settings.LLM_PROVIDER == "gemini":
                file_payloads.append({"data": data, "mime_type": file.mime_type})
        except Exception as exc:
            logger.exception(
                "Failed to extract text from assignment file: assignment_id=%s file_id=%s",
                assignment.id,
                file.id,
            )
            # We continue even if one file fails, using whatever text was extracted

    combined_text = "\n\n".join(text for text in extracted_texts if text.strip())
    
    logger.info("Extracted text length: %d", len(combined_text))
    # print(f"DEBUG: Extracted text length: {len(combined_text)}")
    
    if not combined_text.strip() and not file_payloads:
        # If no text and no files (if using Gemini), we can't proceed
        raise AssignmentAnalysisError("Assignment content was empty after extraction")

    # If sending files to Gemini, we don't need to embed the text in the prompt
    prompt_text = combined_text
    files_to_send = None
    
    if settings.LLM_PROVIDER == "gemini" and file_payloads:
         prompt_text = "Refer to the attached documents for the assignment content."
         files_to_send = file_payloads

    prompt = build_assignment_extraction_prompt(prompt_text)
    try:
        print("DEBUG: Calling Gemini..." if settings.LLM_PROVIDER == "gemini" else "DEBUG: Calling Ollama...")
        raw = generate_text(prompt, files=files_to_send)
        print(f"DEBUG: LLM returned: {raw[:200]}...")
    except Exception as exc:
        logger.exception("Assignment analysis LLM failure: assignment_id=%s", assignment.id)
        raise AssignmentAnalysisError("Analysis service unavailable") from exc
    logger.info("Assignment extraction raw output: %s", raw)
    payload = _parse_llm_json(raw)
    normalized = _validate_extraction_payload(payload)
    concept_payloads = normalized["concepts"]
    question_payloads = normalized["questions"]
    question_concepts = normalized["question_concepts"]
    assignment_concepts = normalized["assignment_concepts"]

    if not concept_payloads and not question_payloads:
        logger.warning("Extraction produced no structured data for assignment %s", assignment.id)
        return AssignmentStructureReviewRead(
            assignment_id=assignment.id,
            concepts=[
                ConceptPayload(id=concept.id, name=concept.name, description=concept.description)
                for concept in assignment.concepts
            ],
            questions=[
                AssignmentQuestionPayload(
                    id=question.id,
                    prompt=question.prompt,
                    position=question.position,
                    concept_ids=[concept.id for concept in question.concepts],
                )
                for question in assignment.questions
            ],
            question_concepts=[
                QuestionConceptLink(question_id=question.id, concept_id=concept.id)
                for question in assignment.questions
                for concept in question.concepts
            ],
            assignment_concepts=[
                AssignmentConceptLink(concept_id=concept.id) for concept in assignment.concepts
            ],
            structure_approved=assignment.structure_approved,
        )

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


def apply_assignment_structure(
    db: Session, assignment: Assignment, payload: AssignmentStructureReview
) -> AssignmentStructureReviewRead:
    concept_responses: list[ConceptPayload] = []
    question_responses: list[AssignmentQuestionPayload] = []

    assignment.questions.clear()
    assignment.concepts.clear()
    db.flush()

    concept_map: dict[int, Concept] = {}
    concept_key_map: dict[str, Concept] = {}
    for concept_payload in payload.concepts:
        concept_obj = None
        if concept_payload.id is not None:
            concept_obj = db.get(Concept, concept_payload.id)
        if concept_obj is None and concept_payload.name:
            concept_obj = db.query(Concept).filter(Concept.name == concept_payload.name).one_or_none()
        if concept_obj is None:
            concept_obj = Concept(name=concept_payload.name, description=concept_payload.description)
            db.add(concept_obj)
        else:
            concept_obj.name = concept_payload.name
            concept_obj.description = concept_payload.description
        db.flush()
        concept_map[concept_obj.id] = concept_obj
        concept_key_map[str(concept_payload.id or concept_payload.name)] = concept_obj
        concept_responses.append(
            ConceptPayload(id=concept_obj.id, name=concept_obj.name, description=concept_obj.description)
        )

    question_map: dict[int, AssignmentQuestion] = {}
    question_key_map: dict[str, AssignmentQuestion] = {}
    for question_payload in payload.questions:
        question_obj = None
        if question_payload.id is not None:
            question_obj = db.get(AssignmentQuestion, question_payload.id)
            if question_obj and question_obj.assignment_id != assignment.id:
                question_obj = None
        if question_obj is None:
            question_obj = AssignmentQuestion(assignment_id=assignment.id, prompt=question_payload.prompt)
            db.add(question_obj)
        question_obj.prompt = question_payload.prompt
        question_obj.position = question_payload.position
        db.flush()
        question_map[question_obj.id] = question_obj
        question_key_map[str(question_payload.id or question_payload.prompt)] = question_obj
        question_responses.append(
            AssignmentQuestionPayload(
                id=question_obj.id,
                prompt=question_obj.prompt,
                position=question_obj.position,
                concept_ids=list(question_payload.concept_ids),
            )
        )

    question_concept_links: list[QuestionConceptLink] = []
    if payload.question_concepts:
        for link in payload.question_concepts:
            question_obj = question_key_map.get(str(link.question_id))
            concept_obj = concept_key_map.get(str(link.concept_id))
            if not question_obj or not concept_obj:
                continue
            question_obj.concepts.append(concept_obj)
            question_concept_links.append(
                QuestionConceptLink(question_id=question_obj.id, concept_id=concept_obj.id)
            )
    else:
        for question_payload in payload.questions:
            question_obj = question_key_map.get(str(question_payload.id or question_payload.prompt))
            if not question_obj:
                continue
            for concept_id in question_payload.concept_ids:
                concept_obj = concept_map.get(concept_id)
                if not concept_obj:
                    continue
                question_obj.concepts.append(concept_obj)
                question_concept_links.append(
                    QuestionConceptLink(question_id=question_obj.id, concept_id=concept_obj.id)
                )

    if payload.assignment_concepts:
        assignment.concepts = [
            concept_map[link.concept_id]
            for link in payload.assignment_concepts
            if link.concept_id in concept_map
        ]
    else:
        assignment.concepts = list(concept_map.values())
    assignment_concept_links = [
        AssignmentConceptLink(concept_id=concept.id) for concept in assignment.concepts
    ]

    for response in question_responses:
        response.concept_ids = [
            link.concept_id for link in question_concept_links if link.question_id == response.id
        ]

    assignment.structure_approved = True
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


async def score_assignment_understanding(
    db: Session, assignment: Assignment
) -> list[UnderstandingScore]:
    questions = list(assignment.questions)
    concepts = list(assignment.concepts)
    chat_logs = (
        db.query(ChatLog)
        .filter(ChatLog.assignment_id == assignment.id)
        .order_by(ChatLog.created_at.asc())
        .all()
    )
    if not chat_logs:
        raise AssignmentAnalysisError("Assignment has no chat logs to score")

    prompt_payload = {
        "assignment_id": assignment.id,
        "questions": [
            {"id": question.id, "prompt": question.prompt, "position": question.position}
            for question in questions
        ],
        "concepts": [
            {"id": concept.id, "name": concept.name, "description": concept.description}
            for concept in concepts
        ],
        "chat_logs": [
            {
                "student_id": log.student_id,
                "question": log.question,
                "created_at": log.created_at.isoformat(),
            }
            for log in chat_logs
        ],
    }
    prompt = build_assignment_scoring_prompt(prompt_payload)
    raw = generate_text(prompt)
    logger.info("Assignment scoring raw output: %s", raw)
    payload = _parse_llm_json(raw)
    score_entries = _normalize_score_entries(payload.get("scores"))

    if not score_entries:
        logger.warning("No valid scores produced for assignment %s", assignment.id)
        return []

    db.query(UnderstandingScore).filter(
        UnderstandingScore.assignment_id == assignment.id
    ).delete(synchronize_session=False)

    scores: list[UnderstandingScore] = []
    for entry in score_entries:
        score = UnderstandingScore(
            student_id=entry["student_id"],
            assignment_id=assignment.id,
            question_id=entry.get("question_id"),
            concept_id=entry.get("concept_id"),
            score=float(entry["score"]),
            confidence=entry.get("confidence"),
            source=entry.get("source"),
        )
        db.add(score)
        scores.append(score)

    db.commit()
    for score in scores:
        db.refresh(score)
    return scores
