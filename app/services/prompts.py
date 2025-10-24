import re
from app.schemas.prompts import PromptRequest
from app.RAG.rag_config import TOP_K
from langchain_chroma import Chroma
from typing import List

def build_prompt(req: PromptRequest, context_blocks: List[str]) -> str:

    context_text = "\n\n".join(f"[CONTEXT {i+1}]\n{cb}" for i, cb in enumerate(context_blocks))
    print(context_text)

    return (
        "### Input:\n"
        f"[SYSTEM] You are a Socratic tutor. Never reveal final answers. Always end with a question. [/SYSTEM]\n"
        "[USER]\n"
        f"<LEVEL={req.level}><SUBJECT={req.subject}>\n"
        f"Assignment excerpt Q({req.q_number}): {context_text}\n"
        f"{req.user_message} [/USER]\n"
        "### Output:\n"
    )

def clean_quoted_output(text: str) -> str:
    t = text.strip()
    # cut anything after a new section
    t = t.split("\n###", 1)[0].rstrip()
    t = t.rstrip('}').rstrip()

    # prefer the first quoted span if present (handles "..." or “...”)
    import re
    m = re.search(r'["“”]([\s\S]*?)["“”]', t)
    if m:
        return m.group(1).strip()

    # fallback: strip straight quotes at ends if present
    if len(t) >= 2 and t[0] in '"“”' and t[-1] in '"“”':
        return t[1:-1].strip()

    return t

def retrieve_context(db: Chroma, query: str, top_k: int = TOP_K):
    docs = db.similarity_search(query, k=top_k)
    return [d.page_content for d in docs]