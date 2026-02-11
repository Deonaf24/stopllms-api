# rag_ingest.py
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.services.ai.rag.rag_config import PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from fastapi import UploadFile
from io import BytesIO
from pypdf import PdfReader
from app.services.ai.rag.rag_db import update_db


def load_documents(assignment_id: str) -> List[Document]:
    assignment_dir = Path(PDF_DIR) / assignment_id
    loader = PyPDFDirectoryLoader(str(assignment_dir))
    return loader.load()


def split_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    return splitter.split_documents(documents)


def attach_chunk_ids(chunks: List[Document]) -> Tuple[List[Document], List[str]]:
    """
    Stable ID per chunk: "{source}:{page}:{chunk_index}"
    Assumes loader sets metadata['source'] and metadata['page']."""
    ids: List[str] = []
    last_page_id = None
    chunk_index = 0

    for ch in chunks:
        source = ch.metadata.get("source", "unknown_source")
        page = ch.metadata.get("page", 0)
        page_id = f"{source}:{page}"

        if page_id == last_page_id:
            chunk_index += 1
        else:
            chunk_index = 0

        cid = f"{page_id}:{chunk_index}"
        ch.metadata["id"] = cid
        ids.append(cid)
        last_page_id = page_id

    return chunks, ids

async def ingest_file(file: UploadFile, assignment_id: str):
    # read the pdf
    content = await file.read()
    reader = PdfReader(BytesIO(content))

    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        docs.append(Document(page_content=text, metadata={"source": f"upload:{file.filename}", "page": i}))

    chunks = split_documents(docs)
    chunks_with_ids, _ = attach_chunk_ids(chunks)
    added = update_db(chunks_with_ids, assignment_id)
    if added == 0:
        print("[UPDATE] No new chunks.")
    else:
        print(f"[UPDATE] Added {added} new chunks.")

    return added
