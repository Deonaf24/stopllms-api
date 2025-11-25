from app.RAG.rag_db import get_db, clear_db

assignment_id = "demo"

db = get_db(assignment_id)

docs = db.similarity_search("vertex cover LP dual")

clear_db(assignment_id)
