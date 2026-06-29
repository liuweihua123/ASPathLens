"""Valley-free routing policy check on relationship sequences."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValleyFreeOutput:
    is_valid: bool | None
    violation_index: int | None
    violation_pattern: str | None
    explanation_zh: str
    explanation_en: str
    uncertain: bool = False


def _effective_rel(rel: str, same_org: bool) -> str:
    if same_org and rel != "unknown":
        return "internal"
    return rel


def check_valley_free(
    sequence: list[str],
    same_org_flags: list[bool] | None = None,
) -> ValleyFreeOutput:
    """
    Legal pattern: c2p* -> p2p? -> p2c*
    unknown: does not force violation but reduces confidence (handled upstream).
    internal (same-org): not strong violation evidence.
    """
    if len(sequence) < 2:
        return ValleyFreeOutput(
            is_valid=None,
            violation_index=None,
            violation_pattern=None,
            explanation_zh="路径长度不足，无法判断 valley-free。",
            explanation_en="Path too short for valley-free analysis.",
            uncertain=True,
        )

    flags = same_org_flags or [False] * len(sequence)
    eff = [_effective_rel(r, flags[i] if i < len(flags) else False) for i, r in enumerate(sequence)]

    if all(r == "unknown" for r in sequence):
        return ValleyFreeOutput(
            is_valid=None,
            violation_index=None,
            violation_pattern=None,
            explanation_zh="所有边关系均为 unknown，结果为 uncertain。",
            explanation_en="All edges are unknown; result is uncertain.",
            uncertain=True,
        )

    phase = "up"  # up: c2p allowed; flat: after p2p; down: p2c only
    p2p_used = False

    for i, rel in enumerate(eff):
        if rel in ("internal", "unknown"):
            continue
        if rel == "c2p":
            if phase == "down":
                pat = f"{sequence[i-1] if i else '?'} -> c2p"
                return ValleyFreeOutput(
                    is_valid=False,
                    violation_index=i,
                    violation_pattern=_rel_pattern_at(sequence, i - 1, i),
                    explanation_zh=(
                        "路径已经进入 provider-to-customer 下坡阶段，随后又出现 "
                        "customer-to-provider 上坡，可能违反 valley-free 策略。"
                    ),
                    explanation_en=(
                        "The path enters the provider-to-customer downhill phase and then "
                        "returns to a customer-to-provider uphill edge, which may violate "
                        "valley-free policy."
                    ),
                )
            if phase == "flat":
                return ValleyFreeOutput(
                    is_valid=False,
                    violation_index=i,
                    violation_pattern=_rel_pattern_at(sequence, i - 1, i),
                    explanation_zh=(
                        "在 peer-to-peer 横向阶段之后出现 customer-to-provider 上坡，"
                        "可能违反 valley-free 策略。"
                    ),
                    explanation_en=(
                        "A customer-to-provider uphill edge appears after a peer phase, "
                        "which may violate valley-free policy."
                    ),
                )
            phase = "up"
        elif rel == "p2p":
            if phase == "down":
                return ValleyFreeOutput(
                    is_valid=False,
                    violation_index=i,
                    violation_pattern=_rel_pattern_at(sequence, i - 1, i),
                    explanation_zh=(
                        "路径已经进入 provider-to-customer 下坡阶段，随后又出现 "
                        "peer-to-peer，可能不符合 valley-free 策略。"
                    ),
                    explanation_en=(
                        "The path enters the provider-to-customer downhill phase and then "
                        "crosses a peer-to-peer edge, which may violate valley-free policy."
                    ),
                )
            if p2p_used:
                return ValleyFreeOutput(
                    is_valid=False,
                    violation_index=i,
                    violation_pattern="p2p -> p2p",
                    explanation_zh="路径中出现多次 peer-to-peer，可能违反 valley-free 策略。",
                    explanation_en="Multiple peer-to-peer edges may violate valley-free policy.",
                )
            p2p_used = True
            phase = "flat"
        elif rel == "p2c":
            if phase == "up" and i == 0:
                pass
            phase = "down"
        else:
            continue

    return ValleyFreeOutput(
        is_valid=True,
        violation_index=None,
        violation_pattern=None,
        explanation_zh="从 AS 商业关系角度看，路径符合 valley-free 模式。",
        explanation_en="From an AS relationship perspective, the path matches valley-free pattern.",
    )


def _rel_pattern_at(seq: list[str], i: int, j: int) -> str:
    if i < 0 or j >= len(seq):
        return " -> ".join(seq[max(0, i) : j + 1])
    return f"{seq[i]} -> {seq[j]}"