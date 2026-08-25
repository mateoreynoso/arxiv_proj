# ArXiv Semantic Search — Project Layout

## Directory Structure

```
arxiv-semantic-search/
│
├── data/                       # Ignored in .gitignore
│   ├── raw_pdfs/               # Downloaded ArXiv PDFs
│   ├── vector_db/              # Persistent ChromaDB files
│   └── metadata.db             # SQLite paper tracking database
│
├── notebooks/                  # Jupyter notebooks for testing and exploration
│
├── notes/                      # Design notes and planning documents
│
├── src/                        # Core pipeline modules
│   ├── data_ingestion.py       # ArXiv API calls, PDF download, text extraction
│   ├── text_cleaning.py        # Unicode normalization, regex cleaning, chunking
│   ├── embeddings.py           # BGE-Base model + ChromaDB storage
│   ├── metadata_db.py          # SQLAlchemy paper tracking (SQLite)
│   └── retrieval.py            # Query embedding, ChromaDB search, Groq generation
│
├── app/
│   └── main.py                 # Streamlit web interface
│
├── tests/                      # Evaluation scripts
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Roadmap

### Phase 1 — MVP (in progress)

Get text flowing from the ArXiv API to a local UI with full RAG.

| Step | Module | Description | Status |
|---|---|---|---|
| Ingestion | `data_ingestion.py` | ArXiv API search, streaming PDF download, PyMuPDF text extraction | Complete |
| Cleaning | `text_cleaning.py` | NFKC Unicode normalization, regex noise removal (references, watermarks, footnote markers), LangChain chunking (800 chars / 100 overlap) | Complete |
| Embedding | `embeddings.py` | BGE-Base via SentenceTransformer, batched encoding with cosine normalization, persistent ChromaDB storage | Complete |
| Tracking | `metadata_db.py` | SQLAlchemy ORM, Paper model, deduplication via `paper_exists()` before re-ingestion | Complete |
| Retrieval + Generation | `retrieval.py` | BGE asymmetric query encoding, ChromaDB top-k search, Groq LLM answer generation with retrieved context | Complete |
| Streamlit UI | `app/main.py` | Search box, streamed answer display, citations panel | Next |

**Remaining Phase 1 tasks:**
- Build `app/main.py` — search box, answer display, citations sidebar
- Add `search_history` table to `metadata_db.py` (second SQL table + JOIN for CV)
- Ingest a larger corpus of 2D turbulence papers
- Pin `requirements.txt` versions

### Phase 2 — Production Backend

Replace Streamlit with a proper REST API to demonstrate backend engineering skills.

- **FastAPI backend** — `/query`, `/ingest`, `/papers` endpoints
- **HTML + JS frontend** — simple search UI calling the API via `fetch()`
- **SQL pre-filtering** — Streamlit sidebar filters (date range, author) narrow ChromaDB search before vector lookup
- **Docker** — containerise the full app for portable deployment
- **AWS S3 / Azure Blob** — store raw PDFs in the cloud instead of local disk

### Phase 3 — Math-Aware Pipeline (Future)

Swap naive text extraction for a pipeline that preserves equations.

- **Vision-Language Parser** — replace PyMuPDF with Nougat or Mathpix to extract inline and display math as LaTeX
- **Math-Aware Chunking** — ensure equations are never split mid-expression
- **Enhanced Retrieval** — match queries containing variables or mathematical conditions directly to formatted equations in the papers

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data source | ArXiv API (`arxiv` library) |
| PDF parsing | PyMuPDF |
| Embedding model | BGE-Base (`BAAI/bge-base-en-v1.5`) |
| Vector store | ChromaDB (local persistent) |
| SQL ORM | SQLAlchemy 2.0 + SQLite |
| LLM | Groq API (Llama 3) |
| UI (Phase 1) | Streamlit |
| UI (Phase 2) | FastAPI + HTML/JS |