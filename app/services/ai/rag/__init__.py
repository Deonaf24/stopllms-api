import os
import shutil
from fastapi import UploadFile
from io import BytesIO
from pypdf import PdfReader
from langchain_core.documents import Document
from .rag_ingest import split_documents, attach_chunk_ids
from .rag_db import update_db, clear_db


RAG_ROOT = "app/services/rag/chroma_langchain_db" 




def clear_database(assignment_id: str) -> bool:
    return clear_db(assignment_id)
