"""
metadata
Stores the data to an SQL database
init_db(engine)              -> None
add_paper(session, paper)    -> None
paper_exists(session, id)    -> bool
get_all_papers(session)      -> list[Paper]
# SQL Command
record_search(connection,query,number_results)
get_recent_searches(conneciton,limit)
TODO
filter_papers(conn, author, date_from, date_to):
"""

from __future__ import annotations

from src.data_ingestion import PaperRecord

from datetime import datetime, timezone
import json
from sqlalchemy import create_engine, text
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


def init_db(engine: Engine) -> None:
    # creates all tables that don't exist yet; safe to call on every startup
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        sql_prompt = text("""
            CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            searched_time DATETIME, 
            n_results INTEGER
            )
        """)
        conn.execute(sql_prompt)

def add_paper(session: Session, paper: PaperRecord) -> None:

    if paper_exists(session,paper["arxiv_id"]):
        return
    
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

# --- Raw SQL function for practice
def record_search(conn: Connection, 
               query: str, 
               n_result: int) -> None:

    sql_prompt = text("""
        INSERT INTO search_history (query, searched_time, n_results)
        VALUES (:query, :searched_time, :n_results)
        """)
    conn.execute(sql_prompt,
                 {"query":query,
                  "searched_time": datetime.now(timezone.utc),
                  "n_results": n_result})
    conn.commit()

def get_recent_searches(conn: Connection,
               limit: int) -> None:

    sql_prompt = text("""
                    SELECT * FROM search_history
                    ORDER BY searched_time DESC
                    LIMIT :limit
                    """)

    result = conn.execute(sql_prompt,{"limit":limit})
    return result.mappings().all()

def get_dead_searches(conn: Connection,
                      limit: int) -> None:
    
    sql_prompt  = text("""SELECT * from search_history
        WHERE n_results = 0
        ORDER BY searched_time DESC
        LIMIT :limit
        """)
    
    result = conn.execute(sql_prompt,{"limit":limit})
    return result.mappings().all()

def searches_per_date_range(conn: Connection,
                     start_date: datetime,
                     end_date: datetime) -> None:
    sql_prompt  = text(""" SELECT * FROM search_history
                        WHERE DATE(searched_time) BETWEEN DATE(:start_date) and DATE(:end_date)
                        ORDER BY searched_time DESC
    """)

    result = conn.execute(sql_prompt,{"start_date":start_date,
                                      "end_date":end_date})
    return result.mappings().all()

if __name__ == "__main__":
    # Manual smoke test — hits the live ArXiv API.
    # Unit tests (no network) live in tests/test_metadata_db.py
    from src.data_ingestion import ingest

    engine = create_engine(DB_PATH, echo=True)
    init_db(engine)

    with Session(engine) as session:
        for paper in ingest("2D Turbulence", max_results=1):
            if paper_exists(session, paper["arxiv_id"]):
                print(f"{paper['arxiv_id']} already in DB — skipping")
            else:
                add_paper(session, paper)
                print(f"Added: {paper['arxiv_id']}")
