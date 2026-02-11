# rag_db.py
from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import List, Tuple, Set
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from app.RAG.rag_config import DB_DIR, EMBED_MODEL
import re

RAG_ROOT = "RAG/chroma_langchain_db" 

def make_safe(name: str) -> str:
    # Lowercase, remove leading/trailing spaces
    name = name.strip().replace(" ", "_")
    # Replace ANY illegal character with underscore
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return name

def get_embeddings():
    return OllamaEmbeddings(model=EMBED_MODEL)


def get_db(assignment_id: str) -> Chroma:
    persist_dir = Path(DB_DIR) / assignment_id
    persist_dir.mkdir(parents=True, exist_ok=True)
    safe_name = make_safe(assignment_id)
    return Chroma(
        persist_directory=str(persist_dir),
        collection_name=f"assignment_{safe_name}",
        embedding_function=get_embeddings(),
    )


def get_existing_ids(db: Chroma) -> Set[str]:
    # include=[] → fetch only ids (works across common LC/Chroma versions)
    got = db.get(include=[])
    return set(got.get("ids", []))


def init_db(chunks_with_ids: List[Document], ids: List[str], assignment_id: str) -> int:
    db = get_db(assignment_id)
    if not ids:
        return 0
    db.add_documents(chunks_with_ids, ids=ids)
    return len(ids)


def diff_new(chunks_with_ids: List[Document], existing_ids: Set[str]) -> Tuple[List[Document], List[str]]:
    new_chunks = [c for c in chunks_with_ids if c.metadata.get("id") not in existing_ids]
    new_ids = [c.metadata["id"] for c in new_chunks]
    return new_chunks, new_ids


def update_db(chunks_with_ids: List[Document], assignment_id: str) -> int:
    db = get_db(assignment_id)
    existing_ids = get_existing_ids(db)
    new_chunks, new_ids = diff_new(chunks_with_ids, existing_ids)
    if not new_ids:
        return 0
    db.add_documents(new_chunks, ids=new_ids)
    return len(new_ids)


def clear_db(assignment_id: str) -> bool:
    """Delete all stored documents in the current Chroma collection but keep the collection schema."""
    db = get_db(assignment_id)
    all_ids = list(get_existing_ids(db))
    if not all_ids:
        print("No documents found in the Chroma DB.")
        return False

    db.delete(ids=all_ids)
    return stats_db(assignment_id) == 0


def stats_db(assignment_id: str) -> int:
    db = get_db(assignment_id)
    return len(get_existing_ids(db))

def clear_all_dbs():
    """
    Deletes ALL RAG vector databases (all namespaces).
    """
    if not os.path.exists(RAG_ROOT):
        return

    for name in os.listdir(RAG_ROOT):
        full_path = os.path.join(RAG_ROOT, name)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
    print("All RAG databases cleared.")