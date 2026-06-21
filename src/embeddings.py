"""
embeddings.py
Embeds cleaned text chunks using SciBERT and stores them in ChromaDB.
Public API:
    load_model()                          -> SentenceTransformer
    get_or_create_collection(client)      -> chromadb.Collection
    embed_and_store(chunks, model, col)   -> None
"""
from __future__ import annotations

from src.text_cleaning import Chunk

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
                             collection_name: str = "arxiv_papers"
                             ) -> chromadb.Collection:
  #connect to (or create) a ChromaDB collection named "arxiv_papers"
  return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def embed_and_store(chunks: list[Chunk], 
                   model: SentenceTransformer, 
                   collection: chromadb.Collection):
    
    texts = [c["text"] for c in chunks]
    vector = model.encode(texts, 
                              normalize_embeddings=True,
                              batch_size=32,
                              convert_to_numpy=True,            
                              ).tolist()
    
    for chunk, vec in zip(chunks,vector):
        # Encode using the cosine Similarity
        # Lets normalize the embedding for numerical stability and speed
        collection.add(
            ids       = [f"{chunk['arxiv_id']}_{chunk['chunk_index']}"],
            embeddings= [vec],
            documents = [chunk["text"]],
            metadatas = [{"arxiv_id": chunk["arxiv_id"], "title": chunk["title"], "chunk_index": chunk["chunk_index"]}]
        )

# --- pseudocode ---
#
if __name__ == "__main__":
    #   ingest a few papers -> clean -> chunk -> embed_and_store
    import os
    os.environ["MALLOC_ARENA_MAX"] = "2"

    from src.data_ingestion import ingest
    from src.text_cleaning import chunk_paper

    #   load model
    model = load_model()
    client     = chromadb.PersistentClient(path=str(DB_PATH))
    collection = get_or_create_collection(client)

    # print number of items in collection to verify
    for paper in ingest("ml modeling", max_results=2):
            chunks = list(chunk_paper(paper))
            embed_and_store(chunks, model, collection)
            print(f"{paper['arxiv_id']}  stored {len(chunks)} chunks")

    print(f"\nTotal vectors in collection: {collection.count()}")