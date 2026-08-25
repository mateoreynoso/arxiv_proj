# ArXiv Semantic Search

A retrieval-augmented generation (RAG) pipeline for scientific papers. Ask questions in natural language and get answers grounded in ArXiv literature, with citations.

## What it does

1. **Ingests** ArXiv papers — downloads PDFs and extracts raw text
2. **Cleans** the text — Unicode normalization, noise removal, chunking
3. **Embeds** chunks using BGE-Base and stores vectors in ChromaDB
4. **Retrieves** the most relevant chunks for a user query
5. **Generates** a grounded answer via the Groq LLM API (Llama 3)
6. **Tracks** ingested papers in SQLite to avoid re-processing

## Tech Stack

| Layer | Tool |
|---|---|
| Data source | ArXiv API |
| PDF parsing | PyMuPDF |
| Embedding model | `BAAI/bge-base-en-v1.5` (BGE-Base) |
| Vector store | ChromaDB (local persistent) |
| SQL ORM | SQLAlchemy 2.0 + SQLite |
| LLM | Groq API (Llama 3) |
| UI | Streamlit |

## Project Structure

```
src/
├── data_ingestion.py   # ArXiv API, PDF download, text extraction
├── text_cleaning.py    # Cleaning and chunking pipeline
├── embeddings.py       # BGE-Base embeddings + ChromaDB storage
├── metadata_db.py      # SQLAlchemy paper tracking
└── retrieval.py        # Query embedding, retrieval, LLM generation

app/
└── main.py             # Streamlit UI
```

## Setup

**1. Install dependencies**

For CUDA 13.x (RTX 5000 series / Blackwell):
```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu132
pip install -r requirements.txt
```

For CPU or older GPUs:
```bash
pip install torch
pip install -r requirements.txt
```

**2. Configure environment**

Create a `.env` file in the project root:
```
PYTHONPATH=/path/to/arxiv_proj
GROQ_API_KEY=your_groq_api_key
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

**3. Ingest papers**
```bash
python src/embeddings.py
```

**4. Run the app**
```bash
streamlit run app/main.py
```

## Roadmap

- [x] Ingestion pipeline
- [x] Text cleaning and chunking
- [x] BGE-Base embeddings + ChromaDB
- [x] SQLAlchemy metadata tracking
- [x] Retrieval + Groq generation
- [ ] Streamlit UI
- [ ] Search history (SQL second table)
- [ ] FastAPI REST backend (Phase 2)
- [ ] Docker (Phase 2)
- [ ] AWS S3 / Azure Blob storage (Phase 2)
- [ ] Math-aware PDF parsing with Nougat (Phase 3)