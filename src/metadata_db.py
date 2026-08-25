"""
metadata
Stores the data to an SQL database
init_db(engine)              -> None
add_paper(session, paper)    -> None
paper_exists(session, id)    -> bool
get_all_papers(session)      -> list[Paper]  
"""

from __future__ import annotations

from src.data_ingestion import PaperRecord

from datetime import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy import Connection, Engine, String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, Session


DB_PATH = "sqlite:///data/metadata.db"

class Base(DeclarativeBase):
    pass

class Paper(Base):
    # Main data base to keep the processed data.
    __tablename__ = "papers"

    arxiv_id:   Mapped[str] = mapped_column(String,primary_key=True)
    title:      Mapped[str] = mapped_column(Text)
    authors:    Mapped[str] = mapped_column(Text)
    published_date: Mapped[datetime] = mapped_column(DateTime)
    pdf_path:   Mapped[str] = mapped_column(String)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        authors = json.loads(self.authors)
        return f"Paper(id={self.arxiv_id!r}, title={self.title!r}, author={authors})"

engine = create_engine(DB_PATH, echo=True)

def init_db(engine: Engine) -> None:
    # creates all tables that don't exist yet; safe to call on every startup
    Base.metadata.create_all(engine)

def add_paper(session: Session, paper: PaperRecord) -> None:
    row = Paper(
        arxiv_id       = paper["arxiv_id"],
        title          = paper["title"],
        authors        = json.dumps(paper["authors"]),
        published_date = paper["published_date"],
        pdf_path       = paper["pdf_path"],
        chunk_count    = 0,
    )
    session.add(row)
    session.commit()

def paper_exists(session: Session, arxiv_id: str) -> bool:
    # Return True if the id is in the database
    return  session.get(Paper,arxiv_id) is not None

def get_all_papers(session: Session) -> list[Paper]:
    return session.query(Paper).all()


if __name__ == "__main__":

    from src.data_ingestion import ingest

    # Test engine and table attemps
    engine = create_engine(DB_PATH, echo=True)
    init_db(engine)
    with Session(engine) as session:
        for paper in ingest("2D Turbulence", max_results=1):
            if paper_exists(session, paper["arxiv_id"]):
                print(f"{paper['arxiv_id']} already in DB — skipping")
            else:
                add_paper(session, paper)
                print(f"Added: {paper['arxiv_id']}")