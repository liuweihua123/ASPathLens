"""Batch analysis API."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.batch_analyzer import (
    export_batch_csv,
    export_batch_markdown,
    parse_batch_csv,
    parse_batch_json,
    parse_batch_txt,
    run_batch,
)
from app.state import data_store

router = APIRouter(prefix="/api/batch", tags=["batch"])

DISCLAIMER = (
    "Batch statistics describe AS relationship policy suspiciousness, "
    "not confirmed BGP incidents."
)


class BatchJsonRequest(BaseModel):
    paths: list[str] | None = None
    items: list[dict] | None = None


@router.post("/analyze/json")
def batch_analyze_json(body: BatchJsonRequest):
    service = data_store.analyzer()
    if body.paths:
        rows = parse_batch_json(body.paths)
    elif body.items:
        rows = parse_batch_json(body.items)
    else:
        raise HTTPException(400, "Provide paths or items")
    return _run_batch_response(service, rows)


@router.post("/analyze")
async def batch_analyze_upload(file: UploadFile = File(...)):
    service = data_store.analyzer()
    raw = (await file.read()).decode("utf-8", errors="replace")
    name = (file.filename or "").lower()
    try:
        if name.endswith(".json"):
            rows = parse_batch_json(json.loads(raw))
        elif name.endswith(".csv"):
            rows = parse_batch_csv(raw)
        else:
            rows = parse_batch_txt(raw)
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(400, str(e)) from e
    return _run_batch_response(service, rows)


def _run_batch_response(service, rows):
    if not rows:
        raise HTTPException(400, "No paths to analyze")
    if len(rows) > 5000:
        raise HTTPException(400, "Maximum 5000 paths per batch")
    result = run_batch(service, rows)
    result["disclaimer"] = DISCLAIMER
    return result


@router.post("/export/csv")
def batch_export_csv(payload: dict):
    rows = payload.get("export_rows") or payload.get("results")
    if rows and isinstance(rows[0], dict) and "summary" in rows[0]:
        rows = [r["summary"] for r in rows]
    if not rows:
        raise HTTPException(400, "No export_rows provided")
    return {"csv": export_batch_csv(rows)}


@router.post("/export/markdown")
def batch_export_md(payload: dict):
    return {"markdown": export_batch_markdown(payload)}