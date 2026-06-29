"""ASN explorer API (Phase 1 local data + ASRank enhancement)."""

from fastapi import APIRouter, HTTPException

from app.services.asrank_client import get_asn_profile
from app.state import data_store

router = APIRouter(prefix="/api/asn", tags=["asn"])


@router.get("/{asn}")
def get_asn(asn: str):
    asn = asn.upper().replace("AS", "").strip()
    if not asn.isdigit():
        raise HTTPException(400, "Invalid ASN")
    store = data_store.as2org
    rel = data_store.asrel
    info = store.asn_to_org.get(asn) if store else None
    providers = peers = customers = 0
    if rel:
        for (a, b), r in rel.relationship_map.items():
            if a != asn:
                continue
            if r == "c2p":
                providers += 1
            elif r == "p2p":
                peers += 1
            elif r == "p2c":
                customers += 1
    same_org = []
    if store and info and info.org_id:
        same_org = [a for a in store.org_to_asns.get(info.org_id, []) if a != asn]
    asrank = get_asn_profile(asn)
    return {
        "asn": asn,
        "local": {
            "org_id": info.org_id if info else None,
            "org_name": info.org_name if info else None,
            "as_name": info.as_name if info else None,
            "country": info.country if info else None,
            "provider_count": providers,
            "peer_count": peers,
            "customer_count": customers,
            "same_org_asns": same_org,
            "role_heuristic": _role_heuristic(providers, peers, customers, len(same_org)),
            "role_disclaimer": "This role is a heuristic estimate, not a ground-truth classification.",
        },
        "asrank": asrank,
    }


def _role_heuristic(p: int, pe: int, c: int, same: int) -> str:
    if p == pe == c == 0:
        return "unknown"
    if same >= 5:
        return "large organization / telecom group"
    if c >= 50 and p <= 5:
        return "large transit provider"
    if pe >= 20 and c >= 20:
        return "large ISP / content-heavy network"
    if p >= 10 and c <= 3:
        return "stub / enterprise / access network"
    return "unknown"