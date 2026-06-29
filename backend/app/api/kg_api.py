"""Knowledge Graph API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.kg_builder import (
    build_asn_neighborhood_graph,
    build_org_subgraph,
    build_path_subgraph,
    build_violation_pattern_graph,
)
from app.services.kg_exporter import export_cypher, export_cytoscape, export_graphml, export_json
from app.services.kg_query import find_org_by_name
from app.services.asrank_client import get_asn_profile
from app.services.batch_analyzer import _batch_results
from app.state import data_store

router = APIRouter(prefix="/api/kg", tags=["knowledge-graph"])


@router.get("/asn/{asn}")
def kg_asn(
    asn: str,
    depth: int = Query(1, ge=1, le=2),
    limit: int = Query(50, ge=1, le=300),
    relationship: str = Query("all"),
    include_org: bool = Query(True),
    include_asrank: bool = Query(True),
):
    asn = asn.upper().replace("AS", "").strip()
    if not asn.isdigit():
        raise HTTPException(400, "Invalid ASN")

    asrank = None
    if include_asrank:
        asrank = get_asn_profile(asn)

    graph = build_asn_neighborhood_graph(
        asn=asn,
        asrel=data_store.asrel,
        as2org=data_store.as2org,
        depth=depth,
        limit=limit,
        rel_filter=relationship,
        include_org=include_org,
        asrank=asrank,
    )
    return graph


@router.post("/path-subgraph")
def kg_path(body: dict):
    as_path = body.get("as_path", "")
    use_normalized = body.get("use_normalized", True)
    if not as_path:
        raise HTTPException(400, "Provide as_path")
    result = data_store.analyzer().analyze(as_path, use_normalized)
    graph = build_path_subgraph(result, as2org=data_store.as2org, asrel=data_store.asrel)
    graph["analysis"] = {
        "is_valley_free": result.get("valley_free", {}).get("is_valid"),
        "risk_score": result.get("risk_score", {}).get("score", 0),
        "candidate_leaker": result.get("route_leak_candidate", {}).get("candidate_asn"),
    }
    return graph


@router.get("/org/{org_id}")
def kg_org(org_id: str, limit: int = Query(100, ge=1, le=300)):
    as2org = data_store.as2org
    if not as2org:
        raise HTTPException(503, "AS2Org data not loaded")

    # Resolve: if it looks like an ASN, find its org_id first
    resolved = org_id
    clean = org_id.upper().replace("AS", "").strip()
    if clean.isdigit() and clean not in as2org.org_meta:
        info = as2org.asn_to_org.get(clean)
        if info and info.org_id:
            resolved = info.org_id
        else:
            raise HTTPException(404, f"ASN {clean} has no organization mapping")

    graph = build_org_subgraph(resolved, asrel=data_store.asrel, as2org=as2org, limit=limit)
    if graph.get("meta", {}).get("error"):
        raise HTTPException(404, graph["meta"]["error"])
    return graph


@router.get("/pattern/{pattern}")
def kg_pattern(pattern: str):
    # Look for batch results containing this pattern
    export_rows = []
    for bd in _batch_results.values():
        export_rows.extend(bd.get("export_rows", []))
    graph = build_violation_pattern_graph(pattern, export_rows or None)
    return graph


@router.get("/export")
def kg_export(
    format: str = Query("json", description="json|cytoscape|graphml|cypher"),
    graph_json: str = Query("", description="JSON-encoded graph (POST body preferred)"),
):
    # For GET, accept graph as query param; for real use, POST body is preferred
    if not graph_json:
        return {"message": "Pass graph JSON as ?graph_json=... or use POST /api/kg/export"}
    import json
    try:
        graph = json.loads(graph_json)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid graph JSON")
    return _do_export(graph, format)


@router.post("/export")
def kg_export_post(body: dict):
    graph = body.get("graph")
    fmt = body.get("format", "json")
    if not graph:
        raise HTTPException(400, "Provide graph JSON")
    return _do_export(graph, fmt)


def _do_export(graph: dict, fmt: str):
    if fmt == "cytoscape":
        return export_cytoscape(graph)
    if fmt == "graphml":
        return {"graphml": export_graphml(graph)}
    if fmt == "cypher":
        return {"cypher": export_cypher(graph)}
    return export_json(graph)