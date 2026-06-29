"""Batch AS path analysis and aggregate statistics."""

from __future__ import annotations

import csv
import io
import json
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.services.path_analyzer import PathAnalyzerService

# In-memory store for pattern search follow-up (optional batch_result_id)
_batch_results: dict[str, dict] = {}


@dataclass
class BatchRow:
    path_id: str
    as_path: str


def parse_batch_csv(content: str) -> list[BatchRow]:
    rows: list[BatchRow] = []
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV has no header")
    fields = [f.lower().strip() for f in reader.fieldnames]
    path_col = None
    id_col = None
    for i, name in enumerate(fields):
        if name in ("as_path", "path", "aspath"):
            path_col = reader.fieldnames[i]
        if name in ("path_id", "id", "pathid"):
            id_col = reader.fieldnames[i]
    if not path_col:
        raise ValueError("CSV must include as_path or path column")
    for idx, row in enumerate(reader):
        path = (row.get(path_col) or "").strip()
        if not path:
            continue
        pid = (row.get(id_col) if id_col else None) or str(idx + 1)
        rows.append(BatchRow(path_id=str(pid), as_path=path))
    return rows


def parse_batch_txt(content: str) -> list[BatchRow]:
    rows = []
    for idx, line in enumerate(content.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(BatchRow(path_id=str(idx + 1), as_path=line))
    return rows


def parse_batch_json(payload: Any) -> list[BatchRow]:
    rows = []
    if isinstance(payload, list):
        for idx, item in enumerate(payload):
            if isinstance(item, str):
                rows.append(BatchRow(path_id=str(idx + 1), as_path=item))
            elif isinstance(item, dict):
                pid = str(item.get("path_id", item.get("id", idx + 1)))
                path = item.get("as_path") or item.get("path") or ""
                if path:
                    rows.append(BatchRow(path_id=pid, as_path=str(path)))
    elif isinstance(payload, dict) and "paths" in payload:
        return parse_batch_json(payload["paths"])
    return rows


def _row_export(result: dict, path_id: str, as_path: str) -> dict:
    seq = result.get("relationship_sequence", [])
    vf = result.get("valley_free", {})
    leak = result.get("route_leak_candidate", {})
    cov = result.get("relationship_coverage", {})
    risk = result.get("risk_score", {})
    same_org_count = sum(1 for e in result.get("edges", []) if e.get("same_org"))
    return {
        "path_id": path_id,
        "as_path": as_path,
        "normalized_path": " ".join(result.get("normalized_path", [])),
        "relationship_sequence": " -> ".join(seq),
        "is_valley_free": vf.get("is_valid"),
        "violation_pattern": vf.get("violation_pattern") or "",
        "candidate_leaker_asn": leak.get("candidate_asn") or "",
        "risk_score": risk.get("score", 0),
        "risk_level": risk.get("level", ""),
        "known_edge_ratio": cov.get("known_ratio", 0),
        "same_org_edge_count": same_org_count,
        "unknown_edge_count": cov.get("unknown_edges", 0),
    }


def run_batch(
    service: PathAnalyzerService,
    rows: list[BatchRow],
    store_result: bool = True,
) -> dict:
    details = []
    violation_patterns: Counter = Counter()
    suspicious_asn_events: Counter = Counter()
    unknown_edges: Counter = Counter()
    asn_org: dict[str, str] = {}

    valley_valid = 0
    suspicious_count = 0
    unknown_heavy = 0
    same_org_adjusted = 0

    as2org = service.ctx.as2org

    def org_for(asn: str) -> str:
        if not as2org:
            return ""
        info = as2org.asn_to_org.get(asn)
        return (info.org_name if info else "") or ""

    for row in rows:
        full = service.analyze(row.as_path, use_normalized=True)
        details.append(
            {
                "path_id": row.path_id,
                "as_path": row.as_path,
                "summary": _row_export(full, row.path_id, row.as_path),
                "analysis": full,
            }
        )

        vf = full.get("valley_free", {})
        if vf.get("is_valid") is True:
            valley_valid += 1
        risk = full.get("risk_score", {})
        level = risk.get("level", "")
        if level in ("suspicious", "highly suspicious"):
            suspicious_count += 1
        cov = full.get("relationship_coverage", {})
        if cov.get("known_ratio", 1) < 0.5:
            unknown_heavy += 1
        if full.get("org_level", {}).get("org_level_less_suspicious"):
            same_org_adjusted += 1

        if vf.get("violation_pattern"):
            violation_patterns[vf["violation_pattern"]] += 1

        leak = full.get("route_leak_candidate", {})
        if leak.get("is_candidate") and leak.get("candidate_asn"):
            suspicious_asn_events[leak["candidate_asn"]] += 1
            for n in full.get("as_nodes", []):
                if n.get("asn") == leak["candidate_asn"]:
                    asn_org[leak["candidate_asn"]] = n.get("org_name") or ""

        for e in full.get("edges", []):
            if e.get("relationship") == "unknown":
                key = (e.get("from"), e.get("to"))
                unknown_edges[key] += 1

    top_patterns = [
        {"pattern": p, "count": c}
        for p, c in violation_patterns.most_common(15)
    ]

    top_suspicious = []
    for asn, count in suspicious_asn_events.most_common(20):
        top_suspicious.append(
            {
                "asn": asn,
                "org_name": asn_org.get(asn, ""),
                "count": count,
                "note": "frequently involved in policy-suspicious path transitions",
            }
        )

    top_unknown = []
    for (fa, tb), count in unknown_edges.most_common(20):
        top_unknown.append(
            {
                "from": fa,
                "to": tb,
                "count": count,
                "from_org": org_for(str(fa)),
                "to_org": org_for(str(tb)),
                "same_org": as2org.same_org(str(fa), str(tb)) if as2org else False,
            }
        )

    batch_id = str(uuid.uuid4())
    result = {
        "batch_result_id": batch_id,
        "total_paths": len(rows),
        "valley_free_valid_count": valley_valid,
        "suspicious_count": suspicious_count,
        "unknown_heavy_count": unknown_heavy,
        "same_org_adjusted_count": same_org_adjusted,
        "top_violation_patterns": top_patterns,
        "top_suspicious_asns": top_suspicious,
        "top_unknown_edges": top_unknown,
        "results": details,
        "export_rows": [d["summary"] for d in details],
    }

    if store_result:
        _batch_results[batch_id] = result
    return result


def get_batch_result(batch_id: str) -> dict | None:
    return _batch_results.get(batch_id)


def export_batch_csv(export_rows: list[dict]) -> str:
    if not export_rows:
        return ""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(export_rows[0].keys()))
    writer.writeheader()
    writer.writerows(export_rows)
    return out.getvalue()


def export_batch_markdown(summary: dict) -> str:
    lines = [
        "# ASPathLens Batch Report",
        "",
        f"- Total paths: {summary.get('total_paths', 0)}",
        f"- Valley-free valid: {summary.get('valley_free_valid_count', 0)}",
        f"- Suspicious: {summary.get('suspicious_count', 0)}",
        f"- Unknown-heavy: {summary.get('unknown_heavy_count', 0)}",
        "",
        "## Top violation patterns",
        "",
    ]
    for item in summary.get("top_violation_patterns", [])[:10]:
        lines.append(f"- {item['pattern']}: {item['count']}")
    lines.extend(["", "## Disclaimer", "", summary.get("disclaimer", "")])
    return "\n".join(lines)