"""
app/main.py
Streamlit UI for the ArXiv semantic search RAG pipeline.
Loads the embedding model, ChromaDB collection, Groq client, and SQL engine
once at startup, then serves queries interactively.
"""
import streamlit as st
from sqlalchemy import create_engine

from src.retrieval import retrieve, generate_prompt, load_model, get_collection, init_bot
from src.metadata_db import init_db, record_search, get_recent_searches, DB_PATH


@st.cache_resource
def setup():
    # cache_resource runs once — heavy objects (model, DB connections) are reused across queries
    engine     = create_engine(DB_PATH)
    init_db(engine)
    model      = load_model()
    collection = get_collection()
    client     = init_bot()
    return engine, model, collection, client

engine, model, collection, client = setup()

# --- page config ---
st.set_page_config(page_title="ArXiv Semantic Search", layout="wide")
st.title("ArXiv Semantic Search")
st.caption("Scientific literature on 2D turbulence & coherent structures — powered by BGE-Base + ChromaDB + Groq")

# --- sidebar controls ---
n_results = st.sidebar.slider("Number of retrieved chunks", min_value=3, max_value=20, value=5)

# --- search ---
search_query = st.text_input("Ask a question", placeholder="e.g. inverse energy cascade in 2D turbulence")

if search_query:
    with st.spinner("Retrieving and generating..."):
        chunks = retrieve(search_query, model, collection, top_k=n_results)
        answer = generate_prompt(search_query, chunks, client)
        with engine.begin() as conn:
            record_search(conn, search_query, len(chunks))

    # generated answer
    st.markdown("### Answer")
    st.write(answer)

    # source chunks
    st.markdown("### Sources")
    if not chunks:
        st.warning("No results found. Run the ingestion pipeline first.")
    else:
        for hit in chunks:
            with st.expander(f"[{hit.get('score', 0):.3f}]  {hit.get('title', 'Unknown')}"):
                st.write(hit["text"])
