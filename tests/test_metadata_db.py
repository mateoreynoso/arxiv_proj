"""
tests/test_metadata_db.py
Unit tests for metadata_db — runs entirely in-memory, no network calls.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.metadata_db import (
    init_db, add_paper, paper_exists,
    record_search, get_recent_searches,
    get_dead_searches, searches_per_date_range,
)

SAMPLE_PAPER = {
    "arxiv_id":       "1234.5678",
    "title":          "Test Paper on 2D Turbulence",
    "authors":        ["Author One", "Author Two"],
    "abstract":       "",
    "pdf_path":       "/tmp/test.pdf",
    "raw_text":       "",
    "published_date": datetime(2026, 1, 1, tzinfo=timezone.utc),
}


@pytest.fixture
def db():
    """Fresh in-memory database for every test."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as session, engine.connect() as conn:
        yield session, conn


# --- Paper ORM tests ---

def test_paper_not_exists_initially(db):
    session, _ = db
    assert not paper_exists(session, "1234.5678")


def test_add_paper_and_exists(db):
    session, _ = db
    add_paper(session, SAMPLE_PAPER)
    assert paper_exists(session, "1234.5678")


def test_add_paper_duplicate_is_ignored(db):
    session, _ = db
    add_paper(session, SAMPLE_PAPER)
    add_paper(session, SAMPLE_PAPER)  # should not raise
   
    # Duplicate insert should not create a second row.
    from sqlalchemy import select
    from src.metadata_db import Paper

    results = session.execute(select(Paper)).scalars().all()
    assert len(results) == 1
    
# --- Search history raw SQL tests ---

def test_record_and_retrieve_searches(db):
    _, conn = db
    record_search(conn, "inverse energy cascade", n_result=5)
    record_search(conn, "vortex merging", n_result=3)

    recent = get_recent_searches(conn, limit=20)
    assert len(recent) == 2


def test_get_recent_searches_respects_limit(db):
    _, conn = db
    for i in range(5):
        record_search(conn, f"query {i}", n_result=i)

    recent = get_recent_searches(conn, limit=3)
    assert len(recent) == 3


def test_get_dead_searches(db):
    _, conn = db
    record_search(conn, "normal search",  n_result=4)
    record_search(conn, "failed search",  n_result=0)
    record_search(conn, "another normal", n_result=2)

    dead = get_dead_searches(conn, limit=20)
    assert len(dead) == 1
    assert dead[0]["query"] == "failed search"


def test_searches_per_date_range_excludes_out_of_range(db):
    _, conn = db
    record_search(conn, "in range",  n_result=1)
    record_search(conn, "also in range", n_result=3)

    # Force the last record to 2025
    outside_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
    conn.execute(
        text("""
            UPDATE search_history
            SET searched_time = :d
            WHERE id = (SELECT MAX(id) FROM search_history)
        """),
        {"d": outside_date},
    )
    conn.commit()

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end   = datetime(2028, 1, 1, tzinfo=timezone.utc)
    ranged = searches_per_date_range(conn, start_date=start, end_date=end)

    assert len(ranged) == 1
    assert ranged[0]["query"] == "in range"
