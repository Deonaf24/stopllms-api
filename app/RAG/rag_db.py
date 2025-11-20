# rag_db.py
from __future__ import annotations
from typing import List, Tuple, Set
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from app.RAG.rag_config import DB_DIR, EMBED_MODEL

def get_embeddings():
    return OllamaEmbeddings(model=EMBED_MODEL)

def get_db() -> Chroma:
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=get_embeddings(),
    )

def get_existing_ids(db: Chroma) -> Set[str]:
    # include=[] → fetch only ids (works across common LC/Chroma versions)
    got = db.get(include=[])
    return set(got.get("ids", []))

def init_db(chunks_with_ids: List[Document], ids: List[str]) -> int:
    db = get_db()
    if not ids:
        return 0
    db.add_documents(chunks_with_ids, ids=ids)
    return len(ids)

def diff_new(chunks_with_ids: List[Document], existing_ids: Set[str]) -> Tuple[List[Document], List[str]]:
    new_chunks = [c for c in chunks_with_ids if c.metadata.get("id") not in existing_ids]
    new_ids = [c.metadata["id"] for c in new_chunks]
    return new_chunks, new_ids

def update_db(chunks_with_ids: List[Document]) -> int:
    db = get_db()
    existing_ids = get_existing_ids(db)
    new_chunks, new_ids = diff_new(chunks_with_ids, existing_ids)
    if not new_ids:
        return 0
    db.add_documents(new_chunks, ids=new_ids)
    return len(new_ids)

def clear_db() -> bool:
    """Delete all stored documents in the current Chroma collection but keep the collection schema."""
    db = get_db()
    all_ids = list(get_existing_ids(db))
    if not all_ids:
        print("No documents found in the Chroma DB.")
        return

    db.delete(ids=all_ids)
    if (stats_db() == 0):
        return True
    else:
        return False


def stats_db() -> int:
    db = get_db()
    return len(get_existing_ids(db))
