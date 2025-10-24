from RAG.rag_db import get_db

db = get_db()

docs = db.similarity_search("vertex cover LP dual")
print(docs[0].page_content)