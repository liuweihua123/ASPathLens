"""Dataset load status — enriched with in-memory parsed stats."""

from __future__ import annotations

import re
from pathlib import Path

from app.config import ASORG_RAW_DIR, ASREL_RAW_DIR, get_settings
from app.db.database import get_connection, init_db
from app.services.asrank_client import asrank_health_check


def _find_latest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = list(directory.glob(pattern))
    if not files:
        return None

    def key(path: Path) -> tuple[str, float]:
        match = re.search(r"(\d{8})", path.name)
        version = match.group(1) if match else ""
        return (version, path.stat().st_mtime)

    return max(files, key=key)


def get_dataset_status(asrel=None, as2org=None) -> dict:
    init_db()
    settings = get_settings()
    asrel_file = _find_latest_file(ASREL_RAW_DIR, "*.as-rel2.txt*")
    asorg_file = _find_latest_file(ASORG_RAW_DIR, "*.as-org2info.txt*")

    asrel_status = "missing"
    asorg_status = "missing"
    asrel_info: dict = {}
    asorg_info: dict = {}

    if asrel_file and asrel_file.exists():
        asrel_status = "fresh"
        asrel_info = {
            "file_name": asrel_file.name,
            "file_path": str(asrel_file),
            "size_bytes": asrel_file.stat().st_size,
        }
    if asorg_file and asorg_file.exists():
        asorg_status = "fresh"
        asorg_info = {
            "file_name": asorg_file.name,
            "file_path": str(asorg_file),
            "size_bytes": asorg_file.stat().st_size,
        }

    # In-memory stats when data is parsed and loaded
    if asrel is not None:
        asrel_info["loaded_edge_count"] = asrel.stats.edge_count
        asrel_info["p2c_count"] = asrel.stats.p2c_count
        asrel_info["p2p_count"] = asrel.stats.p2p_count
        asrel_info["unique_asn_count"] = asrel.stats.unique_asn_count
        asrel_info["dataset_date"] = asrel.stats.dataset_date
        asrel_info["version"] = asrel.version

    if as2org is not None:
        asorg_info["loaded_asn_count"] = as2org.stats.asn_count
        asorg_info["org_count"] = as2org.stats.org_count
        asorg_info["country_count"] = as2org.stats.country_count
        asorg_info["dataset_date"] = as2org.stats.dataset_date
        asorg_info["version"] = as2org.version

    api_ok, api_msg = asrank_health_check()

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT dataset_name, version, status, record_count, parsed_at FROM dataset_status"
        ).fetchall()

    return {
        "as_relationship": {
            "status": asrel_status,
            **asrel_info,
        },
        "as2org": {
            "status": asorg_status,
            **asorg_info,
        },
        "asrank_api": {
            "status": "fresh" if api_ok else "api_unreachable",
            "message": api_msg,
            "note": "ASRank enhancement unavailable." if not api_ok else "OK",
        },
        "db_records": [dict(r) for r in rows],
        "disclaimer": (
            "ASPathLens does not confirm BGP hijacks or route leaks. "
            "It only explains AS path policy suspiciousness."
        ),
    }
