"""Validate the RAG corpus before restarting the backend service.

The active architecture has no persisted FAISS index: startup constructs a
fresh BM25 corpus index and performs semantic reranking only for the BM25
candidates. Run this command after translating sources, then restart Uvicorn
once to load the validated corpus into the live process.
"""

import logging

from process import process_all_txts_in_directory
from retrieve import RetrievalManager


def main():
    logging.basicConfig(level=logging.INFO)
    documents = process_all_txts_in_directory()
    if not documents:
        raise RuntimeError("No RAG documents were produced.")

    manager = RetrievalManager()
    manager.setup_retrievers(documents)
    mode = "BM25 + semantic reranking" if manager.embeddings else "BM25 only"
    print(f"Validated RAG corpus with {len(documents)} chunks ({mode}). Restart the backend to activate it.")


if __name__ == "__main__":
    main()
