"""Compare two AS paths (before / after)."""

from __future__ import annotations

from app.services.path_analyzer import PathAnalyzerService


def _summarize_side(result: dict) -> dict:
    return {
        "path": result.get("normalized_path", []),
        "raw_path": result.get("raw_path", []),
        "relationship_sequence": result.get("relationship_sequence", []),
        "org_path": result.get("org_path", []),
        "compressed_org_path": result.get("compressed_org_path", []),
        "valley_free": result.get("valley_free", {}),
        "risk_score": result.get("risk_score", {}).get("score", 0),
        "level": result.get("risk_score", {}).get("level", "normal"),
        "route_leak_candidate": result.get("route_leak_candidate", {}),
    }


def diff_paths(
    service: PathAnalyzerService,
    before_text: str,
    after_text: str,
    use_normalized: bool = True,
) -> dict:
    before_full = service.analyze(before_text, use_normalized)
    after_full = service.analyze(after_text, use_normalized)

    bp = before_full["normalized_path"]
    ap = after_full["normalized_path"]
    b_set, a_set = set(bp), set(ap)

    added = sorted(a_set - b_set)
    removed = sorted(b_set - a_set)

    changed_positions = []
    max_len = max(len(bp), len(ap))
    for i in range(max_len):
        b_asn = bp[i] if i < len(bp) else None
        a_asn = ap[i] if i < len(ap) else None
        if b_asn != a_asn:
            changed_positions.append({"index": i, "before": b_asn, "after": a_asn})

    rel_changes = []
    b_seq = before_full.get("relationship_sequence", [])
    a_seq = after_full.get("relationship_sequence", [])
    for i in range(max(len(b_seq), len(a_seq))):
        br = b_seq[i] if i < len(b_seq) else None
        ar = a_seq[i] if i < len(a_seq) else None
        if br != ar:
            rel_changes.append({"edge_index": i, "before": br, "after": ar})

    org_changes = []
    bo = before_full.get("org_path", [])
    ao = after_full.get("org_path", [])
    for i in range(max(len(bo), len(ao))):
        if (bo[i] if i < len(bo) else None) != (ao[i] if i < len(ao) else None):
            org_changes.append(
                {
                    "index": i,
                    "before_org": bo[i] if i < len(bo) else None,
                    "after_org": ao[i] if i < len(ao) else None,
                }
            )

    b_score = before_full["risk_score"]["score"]
    a_score = after_full["risk_score"]["score"]
    delta = a_score - b_score

    interpretation_en = _interpret_diff(
        delta, added, removed, changed_positions, rel_changes, after_full
    )
    interpretation_zh = _interpret_diff_zh(
        delta, added, removed, changed_positions, rel_changes, after_full
    )

    return {
        "before": _summarize_side(before_full),
        "after": _summarize_side(after_full),
        "before_detail": before_full,
        "after_detail": after_full,
        "diff": {
            "added_asns": added,
            "removed_asns": removed,
            "changed_positions": changed_positions,
            "relationship_changes": rel_changes,
            "organization_changes": org_changes,
            "risk_delta": delta,
            "interpretation_en": interpretation_en,
            "interpretation_zh": interpretation_zh,
        },
        "disclaimer": (
            "Comparisons reflect AS relationship policy suspiciousness only, "
            "not confirmed BGP events."
        ),
    }


def _interpret_diff(
    delta: int,
    added: list,
    removed: list,
    positions: list,
    rel_changes: list,
    after_full: dict,
) -> str:
    parts = []
    if delta > 0:
        parts.append(
            f"The after path has a higher policy suspiciousness score (+{delta})."
        )
    elif delta < 0:
        parts.append(
            f"The after path has a lower policy suspiciousness score ({delta})."
        )
    else:
        parts.append("Risk scores are unchanged between before and after paths.")

    if added:
        parts.append(f"Added ASNs: {', '.join(added)}.")
    if removed:
        parts.append(f"Removed ASNs: {', '.join(removed)}.")
    if rel_changes:
        rc = rel_changes[0]
        parts.append(
            f"Relationship change at edge {rc['edge_index']}: "
            f"{rc['before']} -> {rc['after']}."
        )
    leak = after_full.get("route_leak_candidate", {})
    if leak.get("is_candidate"):
        parts.append(
            f"After path shows potential pattern {leak.get('pattern')} "
            f"(candidate AS{leak.get('candidate_asn')})."
        )
    return " ".join(parts)


def _interpret_diff_zh(
    delta: int,
    added: list,
    removed: list,
    positions: list,
    rel_changes: list,
    after_full: dict,
) -> str:
    parts = []
    if delta > 0:
        parts.append(f"变更后路径的策略可疑度评分升高（+{delta}）。")
    elif delta < 0:
        parts.append(f"变更后路径的策略可疑度评分降低（{delta}）。")
    else:
        parts.append("前后路径风险评分相同。")
    if added:
        parts.append(f"新增 ASN：{', '.join(added)}。")
    if removed:
        parts.append(f"移除 ASN：{', '.join(removed)}。")
    if rel_changes:
        rc = rel_changes[0]
        parts.append(
            f"第 {rc['edge_index']} 跳关系由 {rc['before']} 变为 {rc['after']}。"
        )
    return " ".join(parts)