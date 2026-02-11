import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.school import Assignment, ChatLog, UnderstandingScore
from app.services.ai.llm import generate_text
from app.services.ai.llm_utils import parse_llm_json
from app.services.ai.prompts import build_assignment_scoring_prompt

logger = logging.getLogger(__name__)

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

class AssignmentAnalysisError(Exception):
    """Raised when assignment analysis fails."""

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
    payload = parse_llm_json(raw)
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
