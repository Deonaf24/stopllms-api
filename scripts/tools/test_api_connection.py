
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from RAG.rag_db import get_db, clear_db, clear_all_dbs

assignment_id = "demo"

db = get_db(assignment_id)

docs = db.similarity_search("vertex cover LP dual")

clear_all_dbs()

