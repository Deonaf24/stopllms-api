from fastapi import UploadFile
from io import BytesIO
from pypdf import PdfReader
from langchain_core.documents import Document

from app.RAG.rag_db import update_db
from app.RAG.rag_ingest import attach_chunk_ids, split_documents


async def ingest_file(file: UploadFile):
    #read the pdf
    content = await file.read()
    reader = PdfReader(BytesIO(content))

    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        docs.append(Document(page_content=text, metadata={"source": f"upload:{file.filename}", "page": i}))

    chunks = split_documents(docs)
    chunks_with_ids, _ = attach_chunk_ids(chunks)
    added = update_db(chunks_with_ids)
    if added == 0:
        print("[UPDATE] No new chunks.")
    else:
        print(f"[UPDATE] Added {added} new chunks.")
    
    return added



    


