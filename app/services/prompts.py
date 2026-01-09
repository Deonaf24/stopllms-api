import re
from typing import List
from langchain_chroma import Chroma

from app.schemas.prompts import PromptRequest
from app.RAG.rag_config import TOP_K


def build_prompt(req: PromptRequest, context_blocks: List[str]) -> str:

    context_text = "\n\n".join(f"[CONTEXT {i+1}]\n{cb}" for i, cb in enumerate(context_blocks))

    return (
        "### Input:\n"
        "[SYSTEM]\n"
        "You are a math tutor.\n"
        "- Use [CONTEXT] if present. If it’s missing or insufficient, rely on your math knowledge.\n"
        "- Task type is inferred from the user’s wording:\n"
        "  • EXPLAIN (general/conceptual): explain clearly; final statements allowed; no need to end with a question.\n"
        "  • SOLVE (specific/assignment): be Socratic; do NOT reveal the final result; must end with a question.\n"
        "- Levels:\n"
        "  • L1 = light hints (≤ 2 short sentences).\n"
        "  • L2 = more hands-on (outline + one micro-step; ≤ 6 sentences; still stop short).\n"
        "Keep steps concise and level-appropriate.\n"
        "[/SYSTEM]\n\n"
        "[HISTORY]\n"
        f"{req.history}\n"
        "[/HISTORY]\n\n"
        "[USER]\n"
        f"<SUBJECT={req.subject}><LEVEL={req.level}>\n"
        f"{req.user_message}\n"
        "[/USER]\n\n"
        "[CONTEXT]\n"
        f"{context_text}\n"
        "[/CONTEXT]\n"
        "### Output:\n"
    )


def build_assignment_extraction_prompt(text: str) -> str:
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


def build_assignment_scoring_prompt(payload: dict) -> str:
    return (
        "You are scoring student understanding for an assignment.\n"
        "Return ONLY valid JSON matching this schema:\n"
        "{\n"
        '  "scores": [\n'
        '    {\n'
        '      "student_id": 1,\n'
        '      "question_id": 10,\n'
        '      "concept_id": 5,\n'
        '      "score": 0.75,\n'
        '      "confidence": 0.6,\n'
        '      "source": "ollama"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Question_id or concept_id can be null if not applicable.\n"
        "Scores must be between 0 and 1.\n"
        "Assignment data:\n"
        f"{payload}\n"
    )


def retrieve_context(db: Chroma, query: str, top_k: int = TOP_K, threshold: float = 0.2):
    docs = db.similarity_search_with_score(query, k=top_k)
    filtered_docs = [doc.page_content for doc, score in docs if score >= threshold]
    print(filtered_docs)
    return filtered_docs
