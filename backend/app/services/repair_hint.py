"""Repair hint generator for valley-free violations."""

from __future__ import annotations


def generate_repair_hint(result: dict) -> dict:
    """Given an analysis result, generate a repair hint if valley-free is violated."""
    vf = result.get("valley_free", {})
    if vf.get("is_valid") is not False:
        return {
            "has_repair_hint": False,
            "message_zh": "路径从 AS 关系角度看符合 valley-free，无需修复建议。",
            "message_en": "The path is valley-free valid; no repair hint needed.",
        }

    path = result.get("normalized_path", [])
    seq = result.get("relationship_sequence", [])
    edges = result.get("edges", [])
    nodes = result.get("as_nodes", [])
    idx = vf.get("violation_index", 0)
    pattern = vf.get("violation_pattern", "")

    # Suspicious segment: violation edge and its neighbors
    start = max(0, idx - 1)
    end = min(len(path), idx + 3)
    segment = path[start:end]
    candidate_middle = path[idx + 1] if idx + 1 < len(path) else None
    candidate_org = ""
    for n in nodes:
        if n.get("asn") == candidate_middle:
            candidate_org = n.get("org_name") or ""
            break

    same_org_at_violation = edges[idx].get("same_org", False) if idx < len(edges) else False
    rel_at_violation = edges[idx].get("relationship", "unknown") if idx < len(edges) else "unknown"
    next_rel = seq[idx + 1] if idx + 1 < len(seq) else None

    hints_en = []
    hints_zh = []
    if rel_at_violation != "unknown" and next_rel and next_rel != "unknown":
        hints_en.append(
            f"The path enters the {'downhill' if rel_at_violation == 'p2c' else 'peer'} phase "
            f"and then encounters a {next_rel} edge, which may violate valley-free policy."
        )
        hints_zh.append(
            f"路径进入 {'下坡' if rel_at_violation == 'p2c' else 'peer'} 阶段后，"
            f"出现了 {next_rel} 边，可能违反 valley-free 策略。"
        )
    else:
        hints_en.append("The violation involves one or more unknown edges; interpretation should be cautious.")
        hints_zh.append("违规片段涉及 unknown 关系，解读时应谨慎。")

    if same_org_at_violation:
        hints_en.append("The violation edge connects ASNs from the same organization; treat as weaker evidence.")
        hints_zh.append("违规边两侧 ASN 属于同一组织，可视为较弱证据。")

    hints_en.append(f"Check whether AS{candidate_middle} propagated a route in a policy-inconsistent direction.")
    hints_zh.append(f"建议重点检查 AS{candidate_middle} 是否存在策略不一致的路由传播。")

    return {
        "has_repair_hint": True,
        "suspicious_segment": segment,
        "violation_pattern": pattern,
        "candidate_middle_asn": candidate_middle,
        "candidate_middle_org": candidate_org,
        "same_org_at_violation": same_org_at_violation,
        "hints_en": hints_en,
        "hints_zh": hints_zh,
        "explanation_zh": (
            f"最小可疑片段位于 {' -> '.join(segment)}。"
            f"{'违规边两侧属于同一组织，可能是组织内部路由调度，不应作为强异常证据。' if same_org_at_violation else ''}"
        ),
        "explanation_en": (
            f"Minimum suspicious segment: {' -> '.join(segment)}."
            + (
                " The violation edge connects same-organization ASNs; treat as weaker evidence."
                if same_org_at_violation
                else ""
            )
        ),
        "disclaimer": "This is a policy-based explanation, not a repair of real routing.",
    }