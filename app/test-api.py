from RAG.rag_db import get_db, clear_db, clear_all_dbs

assignment_id = "demo"

db = get_db(assignment_id)

docs = db.similarity_search("vertex cover LP dual")

clear_all_dbs()

