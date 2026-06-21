"""
Streamlit search interface for the ArXiv semantic search pipeline.
"""
import streamlit as st

from src.embeddings import query
from src.metadata_db import init_db

init_db()

st.set_page_config(page_title="ArXiv Semantic Search", layout="wide")
st.title("ArXiv Semantic Search")
st.caption("Scientific literature on 2D turbulence & coherent structures — powered by SciBERT + ChromaDB")

search_query = st.text_input("Search", placeholder="e.g. inverse energy cascade in 2D turbulence")
n_results = st.sidebar.slider("Results", min_value=3, max_value=20, value=8)

if search_query:
    with st.spinner("Retrieving..."):
        hits = query(search_query, n_results=n_results)

    if not hits:
        st.warning("No results found. Run the ingestion pipeline first.")
    else:
        for hit in hits:
            with st.expander(f"[{hit.get('score', 0):.3f}]  {hit.get('title', 'Unknown')}"):
                st.markdown(f"**Authors:** {hit.get('authors', '')}")
                st.markdown(f"**Abstract:** {hit.get('abstract', '')}")
                st.divider()
                st.write(hit["text"])
