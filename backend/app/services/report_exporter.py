"""Report export: JSON, CSV, Markdown."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone

from app.db.database import get_connection, init_db


def generate_markdown_report(result: dict) -> str:
    """Generate a single-path analysis Markdown report."""
    path_str = " -> ".join(result.get("normalized_path", []))
    raw_str = " -> ".join(result.get("raw_path", []))
    org_str = " -> ".join(result.get("org_path", []))
    seq_str = " -> ".join(result.get("relationship_sequence", []))

    vf = result.get("valley_free", {})
    vf_label = "Uncertain" if vf.get("uncertain") else ("Valid" if vf.get("is_valid") else "Suspicious")

    leak = result.get("route_leak_candidate", {})
    risk = result.get("risk_score", {})
    coverage = result.get("relationship_coverage", {})
    versions = result.get("dataset_versions", {})

    lines = [
        "# ASPathLens Report",
        "",
        "## Input Path",
        "",
        path_str,
        "",
        "## Raw Path",
        "",
        raw_str,
        "",
        "## Normalized Path",
        "",
        path_str,
        "",
        "## Organization Path",
        "",
        org_str,
        "",
        "## Relationship Sequence",
        "",
        seq_str,
        "",
        "## Valley-free Result",
        "",
        vf_label,
        "",
    ]
    if vf.get("violation_pattern"):
        lines.extend([f"**Violation pattern:** `{vf['violation_pattern']}`", ""])
    if vf.get("explanation_en"):
        lines.extend([vf["explanation_en"], ""])
    if vf.get("explanation_zh"):
        lines.extend([vf["explanation_zh"], ""])

    lines.extend([
        "## Potential Route Leak Candidate",
        "",
    ])
    if leak.get("is_candidate"):
        lines.extend([
            f"- Candidate ASN: AS{leak.get('candidate_asn', '?')}",
            f"- Pattern: `{leak.get('pattern')}`",
            f"- Confidence: {leak.get('confidence')}",
            "",
            leak.get("explanation_en", ""),
            "",
            leak.get("explanation_zh", ""),
        ])
    else:
        lines.append("No candidate detected.")

    lines.extend([
        "",
        "## Relationship Coverage",
        "",
        f"- Known edges: {coverage.get('known_edges', '?')} / {coverage.get('total_edges', '?')}",
        f"- Coverage level: {coverage.get('coverage_level', '?')}",
        f"- Known ratio: {coverage.get('known_ratio', '?')}",
    ])
    if coverage.get("confidence_note"):
        lines.extend(["", coverage["confidence_note"]])

    lines.extend([
        "",
        "## Risk Score",
        "",
        f"{risk.get('score', '?')} / 100 — **{risk.get('level', '?')}**",
        "",
    ])
    if risk.get("evidence"):
        lines.append("**Evidence:**")
        lines.extend([f"- {e}" for e in risk["evidence"]])

    lines.extend([
        "",
        "## Dataset Version",
        "",
        f"- ASRelationship: {versions.get('as_relationship', 'not loaded')}",
        f"- AS2Org: {versions.get('as2org', 'not loaded')}",
        "",
        "## Disclaimer",
        "",
        risk.get(
            "disclaimer",
            "This report measures AS relationship policy suspiciousness, not confirmed BGP attack probability.",
        ),
    ])

    return "\n".join(lines)


def save_report(report_type: str, input_json: dict, result_json: dict) -> str:
    """Save report to SQLite and return report_id."""
    init_db()
    report_id = uuid.uuid4().hex[:12]
    md = generate_markdown_report(result_json) if report_type == "single" else ""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO analysis_reports (report_id, report_type, input_json, result_json, markdown_report, created_at) VALUES (?,?,?,?,?,?)",
            (report_id, report_type, json.dumps(input_json, ensure_ascii=False), json.dumps(result_json, ensure_ascii=False), md, now),
        )
    return report_id


def get_report(report_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT report_id, report_type, input_json, result_json, markdown_report, created_at FROM analysis_reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "report_id": row["report_id"],
        "report_type": row["report_type"],
        "input_json": json.loads(row["input_json"]) if row["input_json"] else None,
        "result_json": json.loads(row["result_json"]) if row["result_json"] else None,
        "markdown_report": row["markdown_report"],
        "created_at": row["created_at"],
    }