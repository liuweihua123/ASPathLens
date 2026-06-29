"""AS path tokenization and normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.config import MAX_ASN, PRIVATE_ASN_16BIT, PRIVATE_ASN_32BIT


@dataclass
class NormalizeResult:
    raw_path: list[str]
    normalized_path: list[str]
    prepending_detected: bool = False
    prepended_asns: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _split_path(text: str) -> list[str]:
    parts = re.split(r"[\s,\t]+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _normalize_asn_token(token: str) -> str | None:
    t = token.upper().strip()
    if t.startswith("AS"):
        t = t[2:]
    if not t.isdigit():
        return None
    return str(int(t))


def _is_private_asn(asn: int) -> bool:
    if asn == 0:
        return True
    return asn in PRIVATE_ASN_16BIT or asn in PRIVATE_ASN_32BIT


def normalize_as_path(text: str) -> NormalizeResult:
    warnings: list[str] = []
    tokens = _split_path(text)
    if not tokens:
        return NormalizeResult([], [], warnings=["Empty path."])

    raw_path: list[str] = []
    for token in tokens:
        asn = _normalize_asn_token(token)
        if asn is None:
            warnings.append(f"Invalid token: {token}")
            continue
        n = int(asn)
        if n < 0 or n > MAX_ASN:
            warnings.append(f"ASN out of range: {asn}")
            continue
        if _is_private_asn(n):
            warnings.append(f"Private or reserved ASN: AS{asn}")
        raw_path.append(asn)

    if not raw_path:
        return NormalizeResult([], [], warnings=warnings + ["No valid ASNs in path."])

    if len(raw_path) < 2:
        warnings.append("Path has fewer than 2 ASNs; relationship analysis may be limited.")

    # Collapse consecutive prepending (keep first of run)
    normalized: list[str] = []
    prepended: list[dict] = []
    i = 0
    while i < len(raw_path):
        asn = raw_path[i]
        count = 1
        while i + count < len(raw_path) and raw_path[i + count] == asn:
            count += 1
        if count > 1:
            prepended.append({"asn": asn, "repeat_count": count})
        normalized.append(asn)
        i += count

    prepending = len(prepended) > 0
    if prepending:
        for p in prepended:
            warnings.append(f"AS prepending detected for AS{p['asn']} (x{p['repeat_count']})")

    # AS loop (non-consecutive duplicate)
    seen = set()
    for asn in normalized:
        if asn in seen:
            warnings.append(f"Possible AS loop: AS{asn} appears again after other ASNs.")
        seen.add(asn)

    return NormalizeResult(
        raw_path=raw_path,
        normalized_path=normalized,
        prepending_detected=prepending,
        prepended_asns=prepended,
        warnings=warnings,
    )