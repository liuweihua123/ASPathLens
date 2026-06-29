#!/usr/bin/env python3
"""Parse ASRelationship into SQLite (does not remove active version on failure)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import ASREL_RAW_DIR
from app.db.database import get_connection, init_db
from app.services.asrel_loader import parse_asrel_file
from app.services.dataset_status import _find_latest_file


def main():
    init_db()
    path = _find_latest_file(ASREL_RAW_DIR, "*.as-rel2.txt*")
    if not path:
        raise SystemExit("No ASRelationship file in data/raw/as_relationship/")
    store = parse_asrel_file(path)
    version = store.version
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM as_relationships WHERE version = ?", (version,))
        rows = [
            (version, a, b, rel, "caida-serial2")
            for (a, b), rel in store.relationship_map.items()
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO as_relationships (version, asn_a, asn_b, relationship, source) VALUES (?,?,?,?,?)",
            rows,
        )
        conn.execute(
            """
            INSERT INTO dataset_status (dataset_name, version, file_name, file_path, status, record_count, parsed_at, updated_at)
            VALUES ('as_relationship', ?, ?, ?, 'fresh', ?, ?, ?)
            """,
            (version, path.name, str(path), store.stats.edge_count, now, now),
        )
    print(f"Parsed {store.stats.edge_count} directed edges for version {version}")


if __name__ == "__main__":
    main()