"""Organization-level path compression and same-org analysis."""

from __future__ import annotations


def org_path_from_asns(path: list[str], org_name_fn) -> list[str]:
    return [org_name_fn(a) or f"AS{a}" for a in path]


def compress_org_path(org_path: list[str]) -> list[str]:
    if not org_path:
        return []
    out = [org_path[0]]
    for name in org_path[1:]:
        if name != out[-1]:
            out.append(name)
    return out