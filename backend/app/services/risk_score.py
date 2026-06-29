"""Relationship coverage and risk scoring."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.route_leak_patterns import LeakPatternResult
from app.services.valley_free import ValleyFreeOutput


@dataclass
class CoverageResult:
    total_edges: int
    known_edges: int
    unknown_edges: int
    known_ratio: float
    coverage_level: str
    confidence_note: str


def compute_coverage(sequence: list[str], violation_index: int | None) -> CoverageResult:
    total = len(sequence)
    known = sum(1 for r in sequence if r != "unknown")
    unknown = total - known
    ratio = known / total if total else 0.0
    if ratio >= 0.9:
        level = "high"
    elif ratio >= 0.7:
        level = "medium-high"
    elif ratio >= 0.5:
        level = "medium"
    else:
        level = "low"

    note = ""
    if violation_index is not None and total:
        near = False
        for j in (violation_index - 1, violation_index, violation_index + 1):
            if 0 <= j < total and sequence[j] == "unknown":
                near = True
        if near:
            note = (
                "Unknown edge is adjacent to the violation segment; "
                "valley-free confidence is reduced. / "
                "未知边位于违规片段附近，因此 valley-free 判断置信度降低。"
            )
        elif unknown:
            note = "One or more unknown edges exist, but not adjacent to the violation segment."
    return CoverageResult(total, known, unknown, round(ratio, 4), level, note)


def compute_risk_score(
    valley: ValleyFreeOutput,
    leak: LeakPatternResult,
    violation_same_org: bool,
    known_ratio: float,
    path_len: int,
    org_level_less_suspicious: bool,
    multi_violations: int = 0,
) -> dict:
    score = 0
    evidence: list[str] = []

    if valley.is_valid is False:
        score += 50
        evidence.append("+50 Valley-free violation detected")
    if leak.is_candidate:
        score += 20
        evidence.append("+20 Potential route leak pattern detected")
    if valley.is_valid is False and not violation_same_org:
        score += 10
        evidence.append("+10 Violation edge is not same-org")
    elif valley.is_valid is False and violation_same_org:
        score -= 20
        evidence.append("-20 Violation involves same-organization ASNs")

    if known_ratio >= 0.99 and len(evidence) > 0:
        score += 10
        evidence.append("+10 All edges are known")

    if multi_violations > 1:
        score += 5
        evidence.append("+5 Multiple suspicious transitions")

    if known_ratio < 0.7:
        score -= 15
        evidence.append("-15 Unknown edge ratio is high")

    if path_len < 3:
        score -= 10
        evidence.append("-10 Short path; limited evidence")

    if org_level_less_suspicious:
        score = min(score, 59)
        evidence.append("- Org-level compression reduces suspiciousness (cap uncertain)")

    score = max(0, min(100, score))

    if score <= 29:
        level = "normal"
    elif score <= 59:
        level = "uncertain"
    elif score <= 79:
        level = "suspicious"
    else:
        level = "highly suspicious"

    return {
        "score": score,
        "level": level,
        "evidence": evidence,
        "disclaimer": (
            "This score measures AS relationship policy suspiciousness, "
            "not confirmed attack probability."
        ),
    }