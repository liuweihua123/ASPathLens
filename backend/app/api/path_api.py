"""Path analysis API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models import PathAnalyzeRequest, PathNormalizeRequest
from app.services.path_diff import diff_paths
from app.services.path_normalizer import normalize_as_path
from app.state import data_store

router = APIRouter(prefix="/api/path", tags=["path"])


class PathDiffBody(BaseModel):
    before_path: str
    after_path: str
    use_normalized: bool = True


@router.post("/normalize")
def path_normalize(req: PathNormalizeRequest):
    r = normalize_as_path(req.as_path)
    return {
        "raw_path": r.raw_path,
        "normalized_path": r.normalized_path,
        "prepending_detected": r.prepending_detected,
        "prepended_asns": r.prepended_asns,
        "warnings": r.warnings,
    }


@router.post("/analyze")
def path_analyze(req: PathAnalyzeRequest):
    return data_store.analyzer().analyze(req.as_path, req.use_normalized)


@router.post("/diff")
def path_diff(req: PathDiffBody):
    svc = data_store.analyzer()
    out = diff_paths(svc, req.before_path, req.after_path, req.use_normalized)
    # Omit heavy nested copies from default JSON if client only needs summary
    return {
        "before": out["before"],
        "after": out["after"],
        "diff": out["diff"],
        "disclaimer": out["disclaimer"],
        "before_graph": {
            "path": out["before"]["path"],
            "edges": out["before_detail"].get("edges", []),
            "as_nodes": out["before_detail"].get("as_nodes", []),
        },
        "after_graph": {
            "path": out["after"]["path"],
            "edges": out["after_detail"].get("edges", []),
            "as_nodes": out["after_detail"].get("as_nodes", []),
        },
    }