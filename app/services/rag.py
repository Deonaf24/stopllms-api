import os
import shutil
from fastapi import UploadFile
from io import BytesIO
from pypdf import PdfReader
from langchain_core.documents import Document
from app.RAG.rag_ingest import split_documents, attach_chunk_ids
from app.RAG.rag_db import update_db, clear_db


RAG_ROOT = "app/RAG/chroma_langchain_db" 

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


def clear_database(assignment_id: str) -> bool:
    return clear_db(assignment_id)
