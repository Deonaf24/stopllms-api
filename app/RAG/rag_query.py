# rag_query.py
from __future__ import annotations
from typing import List
from langchain_chroma import Chroma
from app.RAG.rag_db import get_db
from app.RAG.rag_config import TOP_K, LLM_MODEL
import ollama
import re


def socratic_prompt(system: str, user_msg: str, context_blocks: List[str]) -> str:
    """
    Builds your ### Input / ### Output frame with retrieved context.
    We’ll just append context under a CONTEXT section for grounding.
    """
    context_text = "\n\n".join(f"[CONTEXT {i+1}]\n{cb}" for i, cb in enumerate(context_blocks))

    return (
        "### Input:\n"
        f"[SYSTEM] {system} [/SYSTEM]\n"
        "[USER]\n"
        f"{user_msg}\n"
        f"\n[CONTEXT]\n{context_text}\n"
        "[/USER]\n"
        "### Output:\n"
    )


def clean_quoted_output(text: str) -> str:
    t = text.strip()
    t = t.split("\n###", 1)[0].rstrip().rstrip('}').rstrip()
    m = re.search(r'["“”]([\s\S]*?)["“”]', t)
    if m:
        return m.group(1).strip()
    if len(t) >= 2 and t[0] in '"“”' and t[-1] in '"“”':
        return t[1:-1].strip()
    return t


def retrieve_context(db: Chroma, query: str, top_k: int = TOP_K) -> List[str]:
    """
    Simple retriever: similarity search, return page_content strings.
    """
    docs = db.similarity_search(query, k=top_k)
    return [d.page_content for d in docs]


def ask_with_rag(question: str, assignment_id: str, system: str = "You are a Socratic tutor. Never reveal final answers. Always end with a question.") -> dict:
    db = get_db(assignment_id)
    ctx = retrieve_context(db, question, TOP_K)
    prompt = socratic_prompt(system=system, user_msg=question, context_blocks=ctx)

    resp = ollama.generate(
        model=LLM_MODEL,
        prompt=prompt,
        stop=["\n###"],  # keep it tidy
    )
    raw = resp.get("response", "")
    answer = clean_quoted_output(raw)
    return {
        "answer": answer,
        "context_used": ctx,  # useful for debugging; drop in prod
        "prompt": prompt,     # useful to inspect; drop in prod
    }
