"""Policy pattern search in batch results."""

from __future__ import annotations

from collections import Counter
from typing import Any


def search_pattern(
    pattern: str,
    batch_export_rows: list[dict] | None = None,
    batch_results: list[dict] | None = None,
) -> dict:
    """Search for a relationship pattern (e.g. 'p2p -> c2p') in batch results."""
    pattern = pattern.strip().lower()
    if " -> " in pattern:
        pair = tuple(pattern.split(" -> ", 1))
    else:
        pair = (pattern,)

    matched_rows = []
    middle_asn_events: Counter = Counter()
    middle_org_events: Counter = Counter()

    rows = batch_export_rows or []
    analyses = batch_results or []

    for row in rows:
        seq_str = row.get("relationship_sequence", "")
        seq = [s.strip() for s in seq_str.split("->")] if seq_str else []
        if _contains_pattern(seq, pair):
            matched_rows.append(row)

    for item in analyses:
        analysis = item.get("analysis", item)
        seq = analysis.get("relationship_sequence", [])
        path = analysis.get("normalized_path", analysis.get("input_path", []))
        nodes = analysis.get("as_nodes", [])
        if not _contains_pattern(seq, pair):
            continue
        # Find middle ASN at each match
        for i in range(len(seq) - len(pair) + 1):
            if tuple(seq[i : i + len(pair)]) == pair:
                mid_idx = i + 1
                if mid_idx < len(path):
                    asn = path[mid_idx]
                    middle_asn_events[asn] += 1
                    org = ""
                    if mid_idx < len(nodes) and isinstance(nodes[mid_idx], dict):
                        org = nodes[mid_idx].get("org_name") or ""
                    middle_org_events[f"{asn} ({org})" if org else asn] += 1

    top_middle = [
        {"asn": asn, "org_name": _org_from_key(asn, middle_org_events), "count": c}
        for asn, c in middle_asn_events.most_common(20)
    ]

    top_orgs = [
        {"org": org, "count": c}
        for org, c in middle_org_events.most_common(20)
    ]

    return {
        "pattern": " -> ".join(pair),
        "matched_paths": len(matched_rows),
        "top_middle_asns": top_middle,
        "top_organizations": top_orgs,
        "matched_ids": [r.get("path_id") for r in matched_rows[:100]],
    }


def _contains_pattern(seq: list[str], pair: tuple[str, ...]) -> bool:
    n = len(pair)
    for i in range(len(seq) - n + 1):
        if tuple(seq[i : i + n]) == pair:
            return True
    return False


def _org_from_key(asn: str, events: Counter) -> str:
    for k in events:
        if k.startswith(asn):
            # Extract org from "ASN (OrgName)" format
            if "(" in k and k.endswith(")"):
                return k.split("(", 1)[1].rstrip(")")
    return ""