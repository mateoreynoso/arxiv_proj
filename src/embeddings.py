"""
embeddings.py
Embeds cleaned text chunks using SciBERT and stores them in ChromaDB.
Public API:
    load_model()                          -> SentenceTransformer
    get_or_create_collection(client)      -> chromadb.Collection
    embed_and_store(chunks, model, col)   -> None
"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path

# BGE-Base is heavily optimized for asymmetric retrieval (short queries -> long documents)
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
DB_PATH = Path(__file__).parent.parent / "data" / "vector_db"

def load_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    return SentenceTransformer(model_name, device="cuda")

def get_or_create_collection(client: chromadb.ClientAPI, 
                             collection_name: str = "arxiv_papers") -> chromadb.Collection:
  #connect to (or create) a ChromaDB collection named "arxiv_papers"
  return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


# --- pseudocode ---
#
#

#
# embed_and_store(chunks, model, collection):
#   for each chunk in chunks:
#       vector = model.encode(chunk["text"])          # 1 x 768 float array
#       collection.add(
#           ids       = [arxiv_id + "_" + chunk_index],
#           embeddings= [vector],
#           documents = [chunk["text"]],
#           metadatas = [{"arxiv_id": ..., "title": ..., "chunk_index": ...}]
#       )
#
# if __name__ == "__main__":
#   load model
#   open ChromaDB client (local persistent path: data/vector_db/)
#   get or create collection
#   ingest a few papers -> clean -> chunk -> embed_and_store
#   print number of items in collection to verify