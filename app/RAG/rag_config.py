"""Configuration settings for RAG components."""

import os
from pathlib import Path

PDF_DIR = Path("/Users/deon/Documents/Models/Icarus-API/app/RAG/data")
DB_DIR = Path("/Users/deon/Documents/Models/Icarus-API/app/RAG/chroma_langchain_db")

# your ollama models
EMBED_MODEL = "mxbai-embed-large"  # Find an Embed model
LLM_MODEL = "icarus-v2"

# chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

# retrieval
TOP_K = 5
SCORE_THRESHOLD = float(os.getenv("RAG_DISTANCE_THRESHOLD", "0.9"))
