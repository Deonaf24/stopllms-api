# rag_ingest.py
from __future__ import annotations
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.RAG.rag_config import PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP

def load_documents() -> List[Document]:
    loader = PyPDFDirectoryLoader(str(PDF_DIR))
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
    Assumes loader sets metadata['source'] and metadata['page'].
    """
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
