# SQL Design Notes

## Current role (metadata_db.py)
One row per paper — tracks what has been ingested to avoid re-downloading and re-embedding.

Table: `papers`
- arxiv_id (PK), title, authors (JSON), published_date, pdf_path, chunk_count, ingested_at

## Elevated role ideas

### 1. Pre-filtering before vector search
User selects filters in the Streamlit sidebar (date range, author name).
SQL narrows the candidate `arxiv_id` set first, then ChromaDB does vector search
only within that subset — faster and more precise than vector search over everything.

### 2. Search history table
Table: `search_history`
- id (PK), query_text, timestamp, top_arxiv_ids (JSON list of returned paper IDs)

Benefits:
- Shows a second table and a JOIN on the CV
- Enables "recent searches" feature in the UI
- Can aggregate: "which papers appear most in search results"

## What SQL does vs ChromaDB
| | SQL | ChromaDB |
|---|---|---|
| Unit | Paper | Chunk |
| Purpose | Track ingestion, filter, history | Vector similarity search |
| Query type | Exact filters, joins | Nearest-neighbour |