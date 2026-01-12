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
        "You are an expert educational content analyzer.\n"
        "Your task: Extract key concepts and all questions/problems from the text content below.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly these keys:\n"
        "1. 'concepts': A list of concept objects. Each must have 'id' (integer), 'name' (string topic), and 'description' (string summary).\n"
        "2. 'questions': A list of question objects. Each must have 'id' (integer), 'prompt' (string text of the question/task), and 'position' (integer order).\n"
        "3. 'question_concepts': A list of links. Each has 'question_id' and 'concept_id'.\n"
        "4. 'assignment_concepts': A list of links. Each has 'concept_id'.\n\n"
        "IMPORTANT:\n"
        "- Extract REAL data from the text. Do not use placeholders.\n"
        "- 'questions' should include any exercises, problems, or numbered tasks found.\n"
        "- Generate a comprehensive description for each concept based on the text.\n\n"
        "Assignment Text:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )


def build_material_extraction_prompt(text: str) -> str:
    return (
        "You are an expert educational content analyzer.\n"
        "Your task: Extract key concepts from the text content below.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly one key: 'concepts'.\n"
        "1. 'concepts': A list of concept objects. Each must have 'name' (string topic) and 'description' (string summary).\n\n"
        "IMPORTANT:\n"
        "- Extract REAL concepts from the text. Do not use placeholders.\n"
        "- Generate a comprehensive description for each concept based on the text.\n\n"
        "Material Text:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )


def build_assignment_scoring_prompt(payload: dict) -> str:
    return (
        "You are scoring student understanding based on chat logs.\n"
        "Return ONLY valid JSON matching this schema exactly. Do not include markdown formatting like ```json ... ``` or any other text.\n"
        "{\n"
        '  "scores": [\n'
        '    {\n'
        '      "student_id": <int>,\n'
        '      "question_id": <int|null>,\n'
        '      "concept_id": <int|null>,\n'
        '      "score": <float 0.0-1.0>,\n'
        '      "confidence": <float 0.0-1.0>,\n'
        '      "source": "gemini"\n'
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


def build_live_event_generation_prompt(concepts: List[str], text: str, time_limit: int) -> str:
    concept_list = ", ".join(concepts)
    return (
        "You are an expert exam creator.\n"
        f"Your task: Generate multiple-choice questions for a {time_limit}-minute live quiz session on the following topics: {concept_list}.\n\n"
        "Output Format: JSON.\n"
        "The JSON object must contain exactly one key: 'questions'.\n"
        "1. 'questions': A list of objects. Each must have:\n"
        "   - 'id': integer (1-indexed)\n"
        "   - 'text': string (the question)\n"
        "   - 'options': list of 4 strings\n"
        "   - 'correct_index': integer (0-3)\n"
        "   - 'explanation': string (short explanation of why it is correct)\n\n"
        "IMPORTANT:\n"
        "- Questions should test understanding of the provided context.\n"
        "- Difficulty should be appropriate for the content level.\n"
        "- Ensure strictly valid JSON output.\n\n"
        "Context Material:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "JSON Response:"
    )
