"""Pattern search, repair hint, and report export API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.batch_analyzer import _batch_results, run_batch, parse_batch_json
from app.services.pattern_search import search_pattern
from app.services.repair_hint import generate_repair_hint
from app.services.report_exporter import generate_markdown_report, get_report, save_report
from app.state import data_store

router = APIRouter(tags=["analysis"])


# ---- Pattern Search ----

class PatternSearchBody(BaseModel):
    pattern: str
    batch_result_id: str | None = None
    paths: list[str] | None = None


@router.post("/api/pattern/search")
def pattern_search(body: PatternSearchBody):
    # If batch_result_id is given, search in that batch
    batch_data = None
    if body.batch_result_id:
        batch_data = _batch_results.get(body.batch_result_id)

    # If paths are given, run a fresh batch
    if not batch_data and body.paths:
        svc = data_store.analyzer()
        rows = parse_batch_json(body.paths)
        batch_data = run_batch(svc, rows)

    if batch_data:
        export_rows = batch_data.get("export_rows", [])
        results = batch_data.get("results", [])
    else:
        # Search in all cached batch results
        export_rows = []
        results = []
        for bd in _batch_results.values():
            export_rows.extend(bd.get("export_rows", []))
            results.extend(bd.get("results", []))

    out = search_pattern(body.pattern, export_rows, results)
    return out


# ---- Repair Hint ----

@router.post("/api/path/repair-hint")
def repair_hint(req: dict):
    """Given a completed analysis result, produce a repair hint.
    Accepts either a full result JSON or triggers a fresh analysis."""
    if "as_path" in req:
        result = data_store.analyzer().analyze(req["as_path"], req.get("use_normalized", True))
    elif "normalized_path" in req:
        result = req
    else:
        raise HTTPException(400, "Provide as_path or full analysis result")
    return generate_repair_hint(result)


# ---- Report Export ----

@router.post("/api/report/export")
def report_export(body: dict):
    result = body.get("result")
    report_type = body.get("report_type", "single")
    fmt = body.get("format", "json")  # json | csv | markdown

    if not result:
        raise HTTPException(400, "Provide result JSON")

    report_id = save_report(report_type, {}, result)

    if fmt == "markdown":
        return {"report_id": report_id, "format": "markdown", "content": generate_markdown_report(result)}
    if fmt == "csv":
        # Flatten to CSV-friendly dict
        flat = _flatten_for_csv(result)
        import csv, io
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=list(flat.keys()))
        w.writeheader()
        w.writerow(flat)
        return {"report_id": report_id, "format": "csv", "content": out.getvalue()}

    return {"report_id": report_id, "format": "json", "content": result}


@router.get("/api/report/{report_id}")
def report_detail(report_id: str):
    report = get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


def _flatten_for_csv(result: dict) -> dict:
    risk = result.get("risk_score", {})
    vf = result.get("valley_free", {})
    leak = result.get("route_leak_candidate", {})
    cov = result.get("relationship_coverage", {})
    return {
        "normalized_path": " ".join(result.get("normalized_path", [])),
        "relationship_sequence": " -> ".join(result.get("relationship_sequence", [])),
        "org_path": " -> ".join(result.get("org_path", [])),
        "is_valley_free": vf.get("is_valid"),
        "violation_pattern": vf.get("violation_pattern") or "",
        "candidate_leaker_asn": leak.get("candidate_asn") or "",
        "leak_confidence": leak.get("confidence", ""),
        "risk_score": risk.get("score", 0),
        "risk_level": risk.get("level", ""),
        "known_edge_ratio": cov.get("known_ratio", 0),
        "evidence": "; ".join(risk.get("evidence", [])),
    }