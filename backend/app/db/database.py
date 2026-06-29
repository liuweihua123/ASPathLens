"""SQLite database helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DB_PATH, DATA_DIR


def ensure_data_dirs() -> None:
    for d in [
        DATA_DIR,
        DATA_DIR / "raw" / "as_relationship",
        DATA_DIR / "raw" / "as_org",
        DATA_DIR / "tmp",
        DATA_DIR / "processed",
        DATA_DIR / "cache",
        DATA_DIR / "reports",
    ]:
        d.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Path | None = None) -> None:
    ensure_data_dirs()
    path = db_path or DB_PATH
    schema_path = Path(__file__).parent / "schema.sql"
    try:
        with sqlite3.connect(path) as conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))
            conn.commit()
    except (OSError, PermissionError):
        # SQLite not available (e.g. read-only filesystem on Vercel)
        pass


@contextmanager
def get_connection(db_path: Path | None = None):
    ensure_data_dirs()
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()