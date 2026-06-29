"""Dataset diff and change alert API."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.config import ASORG_RAW_DIR, ASREL_RAW_DIR
from app.services.dataset_diff import as2org_diff, asrel_diff
from app.services.dataset_status import _find_latest_file
from app.state import data_store

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


def _list_asrel_files() -> list[dict]:
    if not ASREL_RAW_DIR.exists():
        return []
    files = sorted(ASREL_RAW_DIR.glob("*.as-rel2.txt*"), key=lambda p: p.name)
    result = []
    for f in files:
        m = re.search(r"(\d{8})", f.name)
        result.append({"file_name": f.name, "version": m.group(1) if m else f.stem, "path": str(f)})
    return result


def _list_asorg_files() -> list[dict]:
    if not ASORG_RAW_DIR.exists():
        return []
    files = sorted(ASORG_RAW_DIR.glob("*.as-org2info.txt*"), key=lambda p: p.name)
    result = []
    for f in files:
        m = re.search(r"(\d{8})", f.name)
        result.append({"file_name": f.name, "version": m.group(1) if m else f.stem, "path": str(f)})
    return result


@router.get("/diff")
def dataset_diff(
    dataset: str = Query("as_relationship", description="as_relationship or as2org"),
    old_version: str = Query(..., description="Old version date, e.g. 20260501"),
    new_version: str = Query(..., description="New version date, e.g. 20260601"),
):
    if dataset == "as_relationship":
        old = ASREL_RAW_DIR / f"{old_version}.as-rel2.txt.bz2"
        new = ASREL_RAW_DIR / f"{new_version}.as-rel2.txt.bz2"
        if not old.exists():
            raise HTTPException(404, f"Old file not found: {old.name}")
        if not new.exists():
            raise HTTPException(404, f"New file not found: {new.name}")
        return asrel_diff(old, new)

    if dataset == "as2org":
        old = ASORG_RAW_DIR / f"{old_version}.as-org2info.txt.gz"
        new = ASORG_RAW_DIR / f"{new_version}.as-org2info.txt.gz"
        if not old.exists():
            raise HTTPException(404, f"Old file not found: {old.name}")
        if not new.exists():
            raise HTTPException(404, f"New file not found: {new.name}")
        return as2org_diff(old, new)

    raise HTTPException(400, "dataset must be 'as_relationship' or 'as2org'")


@router.get("/changes/{asn}")
def asn_changes(asn: str, version_old: str = "", version_new: str = ""):
    """Return relationship changes for a specific ASN between two versions."""
    if not version_old or not version_new:
        # Use the two most recent versions
        files = _list_asrel_files()
        if len(files) < 2:
            return {"asn": asn, "changes": [], "message": "Need at least 2 ASRelationship versions"}
        old_file = Path(files[-2]["path"])
        new_file = Path(files[-1]["path"])
    else:
        old_file = ASREL_RAW_DIR / f"{version_old}.as-rel2.txt.bz2"
        new_file = ASREL_RAW_DIR / f"{version_new}.as-rel2.txt.bz2"
        if not old_file.exists() or not new_file.exists():
            return {"asn": asn, "changes": [], "message": "Version files not found"}

    diff = asrel_diff(old_file, new_file)
    alerts = []

    for d in diff.get("changed_details", []):
        if d["asn_a"] == asn or d["asn_b"] == asn:
            alerts.append(
                f"Edge {d['asn_a']} <-> {d['asn_b']}: "
                f"{d['old_rel']} -> {d['new_rel']}"
            )

    for entry in diff.get("top_changed_asns", []):
        if entry["asn"] == asn:
            alerts.insert(0, f"Total {entry['changed_edges']} edge changes in this version")
            break

    return {
        "asn": asn,
        "old_version": diff.get("old_version"),
        "new_version": diff.get("new_version"),
        "changes": alerts[:50],
        "total_changes": len(alerts),
    }


@router.get("/versions")
def list_versions():
    return {
        "as_relationship": _list_asrel_files(),
        "as2org": _list_asorg_files(),
    }