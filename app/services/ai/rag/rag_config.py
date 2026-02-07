# rag_config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PDF_DIR = BASE_DIR / "data"
DB_DIR  = BASE_DIR / "chroma_langchain_db"

from app.core.config import settings

# your ollama models
EMBED_MODEL = "mxbai-embed-large"   # Find an Embed model
# LLM configuration is now managed via settings.LLM_PROVIDER
LLM_MODEL = settings.GEMINI_MODEL if settings.LLM_PROVIDER == "gemini" else settings.OLLAMA_MODEL

# chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

# retrieval
TOP_K = 5
