"""Orchestrate full AS path analysis."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.as2org_loader import As2OrgStore
from app.services.asrel_loader import AsRelStore
from app.services.leaker_localization import localize_leaker
from app.services.org_analyzer import compress_org_path, org_path_from_asns
from app.services.path_normalizer import normalize_as_path
from app.services.risk_score import compute_coverage, compute_risk_score
from app.services.route_leak_patterns import detect_route_leak_pattern
from app.services.valley_free import check_valley_free


@dataclass
class AnalyzerContext:
    asrel: AsRelStore | None = None
    as2org: As2OrgStore | None = None
    asrel_label: str = "not loaded"
    as2org_label: str = "not loaded"


class PathAnalyzerService:
    def __init__(self, ctx: AnalyzerContext):
        self.ctx = ctx

    def analyze(self, as_path_text: str, use_normalized: bool = True) -> dict:
        norm = normalize_as_path(as_path_text)
        work_path = norm.normalized_path if use_normalized else norm.raw_path
        if not work_path:
            work_path = norm.raw_path or []

        asrel = self.ctx.asrel
        as2org = self.ctx.as2org

        def org_name(asn: str) -> str:
            if not as2org:
                return ""
            info = as2org.asn_to_org.get(asn)
            return (info.org_name if info else "") or ""

        as_nodes = []
        for asn in work_path:
            info = as2org.asn_to_org.get(asn) if as2org else None
            as_nodes.append(
                {
                    "asn": asn,
                    "org_id": info.org_id if info else None,
                    "org_name": info.org_name if info else None,
                    "as_name": info.as_name if info else None,
                    "country": info.country if info else None,
                }
            )

        edges = []
        sequence = []
        same_org_edges = []
        for i in range(len(work_path) - 1):
            a, b = work_path[i], work_path[i + 1]
            rel = asrel.get_relationship(a, b) if asrel else "unknown"
            same = as2org.same_org(a, b) if as2org else False
            sequence.append(rel)
            same_org_edges.append(same)
            edges.append(
                {
                    "from": a,
                    "to": b,
                    "relationship": rel,
                    "source": "as_relationship" if asrel else "missing_dataset",
                    "same_org": same,
                }
            )

        vf = check_valley_free(sequence, same_org_edges)
        cov = compute_coverage(sequence, vf.violation_index)
        unknown_near = "violation segment" in cov.confidence_note or "违规片段" in cov.confidence_note
        leak = detect_route_leak_pattern(work_path, sequence, same_org_edges, unknown_near)

        violation_same_org = False
        if vf.violation_index is not None and vf.violation_index < len(same_org_edges):
            violation_same_org = same_org_edges[vf.violation_index]

        o_path = org_path_from_asns(work_path, org_name)
        c_path = compress_org_path(o_path)
        org_less = False
        org_expl_zh = ""
        org_expl_en = ""
        if vf.is_valid is False and violation_same_org:
            org_less = True
            org_expl_zh = (
                "AS 级路径存在可疑关系模式，但可疑片段涉及同一组织内的 ASN。"
                "经过组织级压缩后，该路径的策略可疑度降低，可能属于组织内部路由调度。"
            )
            org_expl_en = (
                "AS-level result is suspicious, but the suspicious segment involves ASNs "
                "from the same organization. After organization-level compression, "
                "the path becomes less suspicious."
            )

        risk = compute_risk_score(
            vf,
            leak,
            violation_same_org,
            cov.known_ratio,
            len(work_path),
            org_less,
        )

        leaker = localize_leaker(work_path, leak, org_name)

        return {
            "input_path": work_path,
            "raw_path": norm.raw_path,
            "normalized_path": norm.normalized_path,
            "as_nodes": as_nodes,
            "edges": edges,
            "relationship_sequence": sequence,
            "org_path": o_path,
            "compressed_org_path": c_path,
            "valley_free": {
                "is_valid": vf.is_valid,
                "violation_index": vf.violation_index,
                "violation_pattern": vf.violation_pattern,
                "explanation_zh": vf.explanation_zh,
                "explanation_en": vf.explanation_en,
                "uncertain": vf.uncertain,
            },
            "route_leak_candidate": {
                "is_candidate": leak.is_candidate,
                "candidate_asn": leak.candidate_asn,
                "pattern": leak.pattern,
                "confidence": leak.confidence,
                "explanation_zh": leak.explanation_zh,
                "explanation_en": leak.explanation_en,
            },
            "leaker_localization": leaker,
            "relationship_coverage": {
                "total_edges": cov.total_edges,
                "known_edges": cov.known_edges,
                "unknown_edges": cov.unknown_edges,
                "known_ratio": cov.known_ratio,
                "coverage_level": cov.coverage_level,
                "confidence_note": cov.confidence_note,
            },
            "risk_score": risk,
            "org_level": {
                "org_path": o_path,
                "compressed_org_path": c_path,
                "org_level_less_suspicious": org_less,
                "explanation_zh": org_expl_zh,
                "explanation_en": org_expl_en,
            },
            "dataset_versions": {
                "as_relationship": self.ctx.asrel_label,
                "as2org": self.ctx.as2org_label,
            },
            "normalization_warnings": norm.warnings,
        }