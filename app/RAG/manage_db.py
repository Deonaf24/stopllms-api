# manage_db.py
from __future__ import annotations
import argparse
from rag_ingest import load_documents, split_documents, attach_chunk_ids
from rag_db import init_db, update_db, stats_db


def cmd_init(assignment_id: str):
    docs = load_documents(assignment_id)
    chunks = split_documents(docs)
    chunks_with_ids, ids = attach_chunk_ids(chunks)
    added = init_db(chunks_with_ids, ids, assignment_id)
    print(f"[INIT] Added {added} chunks.")


def cmd_update(assignment_id: str):
    docs = load_documents(assignment_id)
    chunks = split_documents(docs)
    chunks_with_ids, _ = attach_chunk_ids(chunks)
    added = update_db(chunks_with_ids, assignment_id)
    if added == 0:
        print("[UPDATE] No new chunks.")
    else:
        print(f"[UPDATE] Added {added} new chunks.")


def cmd_stats(assignment_id: str):
    total = stats_db(assignment_id)
    print(f"[STATS] Total chunks in DB: {total}")


def main():
    p = argparse.ArgumentParser("Manage Chroma PDF RAG DB")
    p.add_argument("assignment_id", help="Assignment identifier for the RAG collection")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("update")
    sub.add_parser("stats")
    args = p.parse_args()

    if args.cmd == "init":
        cmd_init(args.assignment_id)
    elif args.cmd == "update":
        cmd_update(args.assignment_id)
    elif args.cmd == "stats":
        cmd_stats(args.assignment_id)


if __name__ == "__main__":
    main()
