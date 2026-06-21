"""
text_cleaning.py
Loads the locally downloaded raw data for cleaning and sectioning
data into chunks
Public API:
    clean(raw_text: str)  -> str
    chunk(paper: dict)    -> Iterator[Chunk]
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, TypedDict
import re

from src.data_ingestion import ingest

from langchain_text_splitters import RecursiveCharacterTextSplitter
import unicodedata


def clean(raw_text: str) -> str:
    text = unicodedata.normalize('NFKC', raw_text)
    text = re.sub(r'\n\s*References\s*\n.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'-\n(\w)', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*arXiv:\S+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Copyright\b.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Received:.*?Accepted:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\u00b6', '', text)

    return text.strip()


class Chunk(TypedDict):
    arxiv_id: str
    chunk_index: int
    text: str
    title: str

def chunk_paper(paper: dict) -> Iterator[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=['\n\n', '\n', '. ', ' ', ''],
    )
    text = clean(paper['raw_text'])
    for i, chunk_text in enumerate(splitter.split_text(text)):
        yield Chunk(
            arxiv_id=paper['arxiv_id'],
            chunk_index=i,
            text=chunk_text,
            title=paper['title'],
        )

if __name__ == "__main__":
    # set test=0 to inspect non-ASCII chars
    # test=1 to check chunking output
    test = 1
    papers = ingest("ml", max_results=3)

    match test:
        case 0:
            for paper in papers:
                text = clean(paper['raw_text'])
                disp = 0
                for i, char in enumerate(text):
                    if ord(char) > 127:
                        if  disp > 2:
                            break
                        disp += 1
                        context = text[max(0, i-15):i+15].replace('\n', '↵')
                        print(f"U+{ord(char):04X}  {unicodedata.name(char, '?'):30s} {char}  ...{context}...")

        case 1:
            for paper in papers:
                chunks = list( chunk_paper(paper))
                print(f"{paper['arxiv_id']}  →  {len(chunks)} chunks")
                for c in chunks[:2]:
                    print(f"  [{c['chunk_index']}] {len(c['text'])} chars: {c['text'][:120]!r}")
                    print()