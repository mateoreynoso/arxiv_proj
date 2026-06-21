"""
data_ingestion.py

Fetches papers from arxiv api, dowloads pdfs to disk
and extract raw text for pipeline.
Public API:
    search_arxiv(query, max_results) -> list[arxiv.Result]
    download_pdf(result, dest_dir)   -> Path
    extract_text(pdf_path)           -> str
    ingest(query, max_results)       -> Iterator[dict]
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import arxiv
import pymupdf
from tqdm import tqdm
import requests

DATA_DIR = Path(__file__).parent.parent / "data"
PDF_DIR = DATA_DIR / "raw_pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

def search_arxiv(query: str, max_results: int = 50) -> list[arxiv.Result]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    results = list(client.results(search))
    return results
    

def download_pdf(result: arxiv.Result, dest_dir: Path = PDF_DIR) -> Path:
    pdf_path = dest_dir/ f"{result. get_short_id()}.pdf"
    if not pdf_path.exists():
        # Stream the request to avoid memory spikes
        with requests.get(result.pdf_url, stream=True) as response:
            response.raise_for_status() # Automatically catch 404s or 500s
            
            # Write the binary data in 8KB chunks
            with open(pdf_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

    return pdf_path


def extract_text(pdf_path: Path) -> str:
    
    doc = pymupdf.open(filename=str(pdf_path))
    return "\n".join(page.get_text() for page in doc)

def ingest(query, max_results) -> Iterator[dict]:

    results = search_arxiv(query=query,max_results=max_results)
    
    for result in results:
        pdf_path = download_pdf(result=result)
        text = extract_text(pdf_path=pdf_path)
        yield {
            "arxiv_id": result.get_short_id(),
            "title": result.title,
            "authors": [str(a) for a in result.authors],
            "abstract": result.summary,
            "pdf_path": str(pdf_path),
            "raw_text": text,
            "published_date": result.published
        }        


if __name__ == "__main__":

    for paper in ingest("2D Turbulence", max_results=3):
        print(paper["arxiv_id"], paper["title"])
        print(paper["raw_text"][:400])
        print("---")