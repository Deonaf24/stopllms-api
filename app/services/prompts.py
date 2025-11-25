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


def retrieve_context(db: Chroma, query: str, top_k: int = TOP_K, threshold: float = 0.9):
    docs = db.similarity_search_with_score(query, k=top_k)
    filtered_docs = [doc.page_content for doc, score in docs if score >= threshold]
    print(filtered_docs)
    return filtered_docs
