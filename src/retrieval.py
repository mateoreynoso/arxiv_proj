"""
retrieval.py
Embeds a user query and retrieves the most relevant chunks from ChromaDB.
Public API:
    retrieve(query, model, collection, top_k) -> list[dict]
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path


load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
api_key = os.getenv("GROQ_API_KEY")
#print(api_key)

import chromadb
from src.embeddings import load_model, DB_PATH

COLLECTION_NAME = "arxiv_papers"

def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(DB_PATH))
    return client.get_collection(COLLECTION_NAME)

def retrieve(query: str,
             model,
             collection: chromadb.Collection,
             top_k: int = 5) -> list[dict]:
    # BGE-Base asymmetric retrieval: prepend instruction for query encoding
    query_vector = model.encode(
        "Represent this sentence for searching relevant passages: " + query,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":      doc,
            "arxiv_id":  meta["arxiv_id"],
            "title":     meta["title"],
            "score":     round(1 - dist, 4),   # cosine distance → similarity
        })

    return chunks

def init_bot() -> Groq:
    bot_client = Groq(api_key=api_key)
    return bot_client

def generate_prompt(query: str, 
                    chunks: list[dict], 
                    bot_client: Groq) -> str:

    context = "\n\n".join(
        f"[{c['title']}]\n{c['text']}" for c in chunks
    )

    response = bot_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a scientific assistant. Answer using only the provided context. If the answer is not in the context, say so."},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    return response.choices[0].message.content

if __name__ == "__main__":

    query = "how does curvature affect turbulent flames?"

    model = load_model()
    collection = get_collection()
    client     = init_bot()

    
    chunks = retrieve(query, model, collection)
    answer = generate_prompt(query, chunks, client)

    print(answer)   