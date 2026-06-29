"""Potential route leak pattern detection (not confirmation)."""

from __future__ import annotations

from dataclasses import dataclass

SUSPICIOUS_PAIRS = {
    ("p2c", "c2p"),
    ("p2c", "p2p"),
    ("p2p", "c2p"),
    ("p2p", "p2p"),
}


@dataclass
class LeakPatternResult:
    is_candidate: bool
    candidate_asn: str | None
    pattern: str | None
    confidence: str
    explanation_zh: str
    explanation_en: str
    violation_edge_index: int | None = None


def detect_route_leak_pattern(
    path: list[str],
    sequence: list[str],
    same_org_per_edge: list[bool],
    unknown_near_violation: bool = False,
) -> LeakPatternResult:
    none = LeakPatternResult(
        is_candidate=False,
        candidate_asn=None,
        pattern=None,
        confidence="none",
        explanation_zh="未检测到明确的潜在 route leak 关系模式。",
        explanation_en="No clear potential route leak relationship pattern detected.",
    )
    if len(path) < 3 or len(sequence) < 2:
        return none

    for i in range(len(sequence) - 1):
        a, b = sequence[i], sequence[i + 1]
        if (a, b) not in SUSPICIOUS_PAIRS:
            continue
        same_org = False
        if i < len(same_org_per_edge):
            same_org = same_org_per_edge[i] or (
                i + 1 < len(same_org_per_edge) and same_org_per_edge[i + 1]
            )
        pattern = f"{a} -> {b}"
        middle_idx = i + 1
        candidate = path[middle_idx] if middle_idx < len(path) else None

        known_count = sum(1 for x in (a, b) if x != "unknown")
        confidence = "medium"
        if known_count == 2 and not same_org and not unknown_near_violation:
            confidence = "high"
        elif same_org or unknown_near_violation:
            confidence = "low"

        return LeakPatternResult(
            is_candidate=True,
            candidate_asn=candidate,
            pattern=pattern,
            confidence=confidence,
            violation_edge_index=i,
            explanation_zh=(
                "该模式可能表示策略不一致的路由传播，属于潜在 route leak 线索，"
                "但不能单独证明泄露。"
            ),
            explanation_en=(
                "This pattern may indicate policy-inconsistent route propagation. "
                "It is a potential signal, not a confirmed route leak."
            ),
        )
    return none