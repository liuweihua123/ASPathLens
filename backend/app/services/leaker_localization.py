"""Candidate leaker ASN localization."""

from __future__ import annotations

from app.services.route_leak_patterns import LeakPatternResult


def localize_leaker(
    path: list[str],
    leak: LeakPatternResult,
    org_name_for_asn: callable,
) -> dict:
    if not leak.is_candidate or not leak.candidate_asn:
        return {
            "candidate_asn": None,
            "candidate_org": None,
            "pattern": None,
            "confidence": "none",
            "reason_zh": "",
            "reason_en": "",
            "disclaimer": (
                "This is only a candidate localization based on AS relationship patterns, "
                "not a confirmed leaker."
            ),
        }
    asn = leak.candidate_asn
    org = org_name_for_asn(asn)
    reason_zh = (
        f"AS{asn} 位于可疑关系转换的中间位置（{leak.pattern}），"
        "可能存在策略不一致的传播行为；这仅为候选定位，不能确认泄露者。"
    )
    reason_en = (
        f"AS{asn} sits at a policy-suspicious transition ({leak.pattern}). "
        "This is candidate localization only, not a confirmed leaker."
    )
    return {
        "candidate_asn": asn,
        "candidate_org": org,
        "pattern": leak.pattern,
        "confidence": leak.confidence,
        "reason_zh": reason_zh,
        "reason_en": reason_en,
        "disclaimer": (
            "This is only a candidate localization based on AS relationship patterns, "
            "not a confirmed leaker."
        ),
    }