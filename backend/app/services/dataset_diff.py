"""Dataset diff: compare two ASRelationship or AS2Org versions."""

from __future__ import annotations

import bz2
import gzip
from pathlib import Path
from collections import Counter

from app.services.asrel_loader import _parse_line
from app.services.as2org_loader import parse_as2org_file


def asrel_diff(old_path: Path, new_path: Path) -> dict:
    """Compare two ASRelationship files and produce a diff summary."""
    old_map = _load_asrel_edges(old_path)
    new_map = _load_asrel_edges(new_path)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys

    changed_rel = []
    for k in common:
        if old_map[k] != new_map[k]:
            changed_rel.append({"asn_a": k[0], "asn_b": k[1], "old_rel": old_map[k], "new_rel": new_map[k]})

    affected: Counter = Counter()
    for a, b in added:
        affected[a] += 1
        affected[b] += 1
    for a, b in removed:
        affected[a] += 1
        affected[b] += 1
    for item in changed_rel:
        affected[item["asn_a"]] += 1
        affected[item["asn_b"]] += 1

    type_changes: Counter = Counter()
    for item in changed_rel:
        type_changes[f"{item['old_rel']} -> {item['new_rel']}"] += 1

    import re
    def _date(p: Path) -> str:
        m = re.search(r"(\d{8})", p.name)
        return m.group(1) if m else p.stem

    return {
        "old_version": _date(old_path),
        "new_version": _date(new_path),
        "old_edge_count": len(old_map),
        "new_edge_count": len(new_map),
        "added_edges": len(added),
        "removed_edges": len(removed),
        "changed_relationships": len(changed_rel),
        "type_changes": dict(type_changes.most_common(20)),
        "top_changed_asns": [
            {"asn": asn, "changed_edges": count}
            for asn, count in affected.most_common(20)
        ],
        "changed_details": changed_rel[:100],
    }


def as2org_diff(old_path: Path, new_path: Path) -> dict:
    """Compare two AS2Org files."""
    old = parse_as2org_file(old_path)
    new = parse_as2org_file(new_path)

    old_asns = set(old.asn_to_org.keys())
    new_asns = set(new.asn_to_org.keys())
    common = old_asns & new_asns

    asn_org_changed = 0
    org_name_changed = 0
    country_changed = 0

    for asn in common:
        o = old.asn_to_org[asn]
        n = new.asn_to_org[asn]
        if o.org_id != n.org_id:
            asn_org_changed += 1
        if o.country != n.country:
            country_changed += 1

    old_orgs = set(old.org_meta.keys())
    new_orgs = set(new.org_meta.keys())
    for oid in old_orgs & new_orgs:
        if old.org_meta[oid].get("org_name") != new.org_meta[oid].get("org_name"):
            org_name_changed += 1

    return {
        "old_version": old.version,
        "new_version": new.version,
        "old_asn_count": len(old_asns),
        "new_asn_count": len(new_asns),
        "new_asns": len(new_asns - old_asns),
        "removed_asns": len(old_asns - new_asns),
        "asn_org_changed": asn_org_changed,
        "org_name_changed": org_name_changed,
        "country_changed": country_changed,
    }


def _load_asrel_edges(path: Path) -> dict[tuple[str, str], str]:
    """Load edges into {(asn_a, asn_b): relationship}."""
    edges: dict[tuple[str, str], str] = {}
    is_bz2 = path.name.endswith(".bz2")
    opener = bz2.open if is_bz2 else open
    mode = "rt" if is_bz2 else "r"
    with opener(path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = _parse_line(line)
            if not parsed:
                continue
            a, b, rel = parsed
            edges[(a, b)] = rel
    return edges