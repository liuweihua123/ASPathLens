"""Knowledge Graph queries — reads from loaded ASRel + AS2Org stores."""

from __future__ import annotations

from typing import Any


# ---- Node factories ----

def make_asn_id(asn: str) -> str:
    return f"asn:{asn}"


def make_org_id(org_id: str) -> str:
    return f"org:{org_id}"


def make_country_id(code: str) -> str:
    return f"country:{code}"


def make_pattern_id(pattern: str) -> str:
    return f"pattern:{pattern.replace(' ', '')}"


def make_path_id(path_id: str) -> str:
    return f"path:{path_id}"


def make_segment_id(asns: list[str]) -> str:
    return f"seg:{'-'.join(asns)}"


def make_edge_id(src: str, dst: str, etype: str) -> str:
    return f"{etype.lower()}:{src.split(':')[-1]}-{dst.split(':')[-1]}"


# ---- Build single nodes ----

def get_asn_node(asn: str, as2org=None, asrank: dict | None = None) -> dict:
    info = as2org.asn_to_org.get(asn) if as2org else None
    props: dict[str, Any] = {
        "asn": asn,
        "org_id": info.org_id if info else None,
        "org_name": info.org_name if info else None,
        "as_name": info.as_name if info else None,
        "country": info.country if info else None,
    }
    if asrank and asrank.get("available"):
        props["rank"] = asrank.get("rank")
        props["degree"] = asrank.get("degree")
    return {
        "id": make_asn_id(asn),
        "type": "ASN",
        "label": f"AS{asn}",
        "properties": props,
    }


def get_org_node(org_id: str, as2org) -> dict:
    meta = as2org.org_meta.get(org_id, {})
    members = as2org.org_to_asns.get(org_id, [])
    return {
        "id": make_org_id(org_id),
        "type": "Organization",
        "label": meta.get("org_name") or org_id,
        "properties": {
            "org_id": org_id,
            "org_name": meta.get("org_name", ""),
            "country": meta.get("country", ""),
            "asn_count": len(members),
        },
    }


def get_country_node(code: str, as2org) -> dict:
    asn_count = 0
    org_set: set[str] = set()
    for asn, info in as2org.asn_to_org.items():
        if info.country == code:
            asn_count += 1
            if info.org_id:
                org_set.add(info.org_id)
    return {
        "id": make_country_id(code),
        "type": "Country",
        "label": code,
        "properties": {"country_code": code, "asn_count": asn_count, "org_count": len(org_set)},
    }


def get_violation_pattern_node(pattern: str) -> dict:
    desc_map = {
        "p2c -> c2p": "Downhill then uphill — valley-free violation",
        "p2c -> p2p": "Downhill then peer — may indicate leak",
        "p2p -> c2p": "Peer then uphill — potential route leak signal",
        "p2p -> p2p": "Multiple peer edges — valley-free violation",
    }
    sev_map = {"p2p -> c2p": "medium", "p2c -> c2p": "high", "p2c -> p2p": "medium", "p2p -> p2p": "medium"}
    return {
        "id": make_pattern_id(pattern),
        "type": "ViolationPattern",
        "label": pattern,
        "properties": {
            "pattern": pattern,
            "description": desc_map.get(pattern, "Suspicious relationship transition"),
            "severity": sev_map.get(pattern, "low"),
        },
    }


# ---- Neighbor queries ----

def get_asn_neighbors(asn: str, asrel, as2org, depth: int = 1, limit: int = 50, rel_filter: str = "all") -> dict:
    """Return providers/peers/customers/same-org lists for center ASN."""
    providers, peers, customers, unknowns = [], [], [], []

    if asrel:
        for (a, b), rel in asrel.relationship_map.items():
            if a != asn:
                continue
            entry = {"asn": b, "relationship": rel}
            if rel == "c2p":
                providers.append(entry)
            elif rel == "p2c":
                customers.append(entry)
            elif rel == "p2p":
                peers.append(entry)
            else:
                unknowns.append(entry)

    same_org = []
    if as2org:
        info = as2org.asn_to_org.get(asn)
        if info and info.org_id:
            same_org = [a for a in as2org.org_to_asns.get(info.org_id, []) if a != asn]

    total = len(providers) + len(peers) + len(customers) + len(unknowns)

    # Apply filter
    if rel_filter == "provider":
        selected = providers[:limit]
    elif rel_filter == "peer":
        selected = peers[:limit]
    elif rel_filter == "customer":
        selected = customers[:limit]
    elif rel_filter == "same-org":
        selected = [{"asn": a, "relationship": "same-org"} for a in same_org[:limit]]
    elif rel_filter == "unknown":
        selected = unknowns[:limit]
    else:
        # all: mix proportionally, prioritize up to limit
        pool = []
        # Take providers first (usually small), then peers, then customers
        pool.extend(providers)
        pool.extend(peers)
        pool.extend(customers)
        pool.extend(unknowns)
        selected = pool[:limit]

    return {
        "providers": providers,
        "peers": peers,
        "customers": customers,
        "unknowns": unknowns,
        "same_org": same_org,
        "selected": selected,
        "total_neighbors": total,
    }


def get_org_members(org_id: str, as2org) -> list[str]:
    return as2org.org_to_asns.get(org_id, [])


def get_external_org_neighbors(org_id: str, asrel, as2org, limit: int = 50) -> list[dict]:
    """Return external org→org connections aggregated from ASN-level edges."""
    members = set(as2org.org_to_asns.get(org_id, []))
    ext_orgs: dict[str, dict] = {}  # org_id → {rel_type: count, org_name}

    for (a, b), rel in asrel.relationship_map.items():
        if a in members and b not in members:
            info = as2org.asn_to_org.get(b)
            if not info or not info.org_id:
                continue
            oid = info.org_id
            if oid not in ext_orgs:
                ext_orgs[oid] = {"org_id": oid, "org_name": info.org_name, "p2c": 0, "c2p": 0, "p2p": 0, "unknown": 0}
            if rel == "p2c":
                ext_orgs[oid]["p2c"] += 1
            elif rel == "c2p":
                ext_orgs[oid]["c2p"] += 1
            elif rel == "p2p":
                ext_orgs[oid]["p2p"] += 1
            else:
                ext_orgs[oid]["unknown"] += 1

    result = sorted(ext_orgs.values(), key=lambda x: x["p2c"] + x["p2p"] + x["c2p"], reverse=True)
    return result[:limit]


def find_org_by_name(name: str, as2org) -> str | None:
    """Fuzzy search org by name. Returns org_id or None."""
    name_lower = name.lower().strip()
    for org_id, meta in as2org.org_meta.items():
        if meta.get("org_name", "").lower() == name_lower:
            return org_id
    # Partial match
    for org_id, meta in as2org.org_meta.items():
        if name_lower in meta.get("org_name", "").lower():
            return org_id
    return None