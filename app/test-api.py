from RAG.rag_db import get_db, clear_db

db = get_db()

docs = db.similarity_search("vertex cover LP dual")

clear_db()