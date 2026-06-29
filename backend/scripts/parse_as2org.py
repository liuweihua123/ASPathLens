#!/usr/bin/env python3
"""Parse AS2Org into SQLite."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import ASORG_RAW_DIR
from app.db.database import get_connection, init_db
from app.services.as2org_loader import parse_as2org_file
from app.services.dataset_status import _find_latest_file


def main():
    init_db()
    path = _find_latest_file(ASORG_RAW_DIR, "*.as-org2info.txt*")
    if not path:
        raise SystemExit("No AS2Org file in data/raw/as_org/")
    store = parse_as2org_file(path)
    version = store.version
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM as_orgs WHERE version = ?", (version,))
        conn.execute("DELETE FROM organizations WHERE version = ?", (version,))
        for asn, info in store.asn_to_org.items():
            conn.execute(
                "INSERT OR REPLACE INTO as_orgs (version, asn, as_name, org_id, org_name, country) VALUES (?,?,?,?,?,?)",
                (version, asn, info.as_name, info.org_id, info.org_name, info.country),
            )
        for org_id, meta in store.org_meta.items():
            conn.execute(
                "INSERT OR REPLACE INTO organizations (version, org_id, org_name, country, source) VALUES (?,?,?,?,?)",
                (version, org_id, meta.get("org_name"), meta.get("country"), meta.get("source")),
            )
        conn.execute(
            """
            INSERT INTO dataset_status (dataset_name, version, file_name, file_path, status, record_count, parsed_at, updated_at)
            VALUES ('as2org', ?, ?, ?, 'fresh', ?, ?, ?)
            """,
            (version, path.name, str(path), store.stats.asn_count, now, now),
        )
    print(f"Parsed {store.stats.asn_count} ASNs, {store.stats.org_count} orgs")


if __name__ == "__main__":
    main()