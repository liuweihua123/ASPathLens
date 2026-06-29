"""Knowledge Graph builder — assembles subgraphs from query results + analysis."""

from __future__ import annotations

from typing import Any

from app.services.kg_query import (
    get_asn_node,
    get_asn_neighbors,
    get_country_node,
    get_external_org_neighbors,
    get_org_node,
    get_violation_pattern_node,
    make_asn_id,
    make_country_id,
    make_edge_id,
    make_org_id,
    make_path_id,
    make_pattern_id,
    make_segment_id,
    find_org_by_name,
)


def _wrap(nodes: list, edges: list, meta: dict | None = None) -> dict:
    return {"nodes": nodes, "edges": edges, "meta": meta or {}}


# ---- Path subgraph ----

def build_path_subgraph(analysis: dict, as2org=None, asrel=None) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[str] = set()

    path = analysis.get("normalized_path", [])
    as_nodes = analysis.get("as_nodes", [])
    edge_data = analysis.get("edges", [])
    seq = analysis.get("relationship_sequence", [])
    vf = analysis.get("valley_free", {})
    leak = analysis.get("route_leak_candidate", {})
    versions = analysis.get("dataset_versions", {})

    # Path node
    path_id_str = "-".join(path)
    path_node_id = make_path_id(path_id_str)
    risk = analysis.get("risk_score", {})
    nodes.append({
        "id": path_node_id,
        "type": "ASPath",
        "label": f"Path {' → '.join(path)}",
        "properties": {
            "raw_path": " ".join(path),
            "normalized_path": " ".join(path),
            "risk_score": risk.get("score", 0),
            "risk_level": risk.get("level", ""),
            "is_valley_free": vf.get("is_valid"),
        },
    })
    seen_nodes.add(path_node_id)

    # ASN + Org nodes
    for i, asn in enumerate(path):
        nid = make_asn_id(asn)
        if nid not in seen_nodes:
            n = get_asn_node(asn, as2org)
            # Highlight candidate leaker
            if leak.get("is_candidate") and asn == leak.get("candidate_asn"):
                n["properties"]["is_candidate_leaker"] = True
                n["properties"]["candidate_confidence"] = leak.get("confidence")
            nodes.append(n)
            seen_nodes.add(nid)
        # Path → ASN edge
        eid = make_edge_id(path_node_id, nid, "CONTAINS_ASN")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": path_node_id, "target": nid, "type": "CONTAINS_ASN", "properties": {}})
            seen_edges.add(eid)

        # Org node + BELONGS_TO
        n_info = as_nodes[i] if i < len(as_nodes) else {}
        org_id = n_info.get("org_id")
        if org_id:
            oid = make_org_id(org_id)
            if oid not in seen_nodes:
                nodes.append(get_org_node(org_id, as2org))
                seen_nodes.add(oid)
            beid = make_edge_id(nid, oid, "BELONGS_TO")
            if beid not in seen_edges:
                edges.append({"id": beid, "source": nid, "target": oid, "type": "BELONGS_TO", "properties": {}})
                seen_edges.add(beid)

    # Relationship edges
    rel_type_map = {"p2c": "P2C", "c2p": "C2P", "p2p": "P2P", "unknown": "UNKNOWN_REL"}
    for i, e in enumerate(edge_data):
        src = make_asn_id(e["from"])
        dst = make_asn_id(e["to"])
        rel = e.get("relationship", "unknown")
        etype = rel_type_map.get(rel, "UNKNOWN_REL")
        eid = make_edge_id(src, dst, etype)
        if eid not in seen_edges:
            is_violation = False
            if vf.get("violation_index") is not None and i == vf["violation_index"]:
                is_violation = True
            edges.append({
                "id": eid, "source": src, "target": dst, "type": etype,
                "properties": {
                    "relationship": rel,
                    "same_org": e.get("same_org", False),
                    "dataset_version": versions.get("as_relationship", ""),
                    "is_violation_edge": is_violation,
                },
            })
            seen_edges.add(eid)

    # Violation pattern node
    if vf.get("is_valid") is False and vf.get("violation_pattern"):
        pnid = make_pattern_id(vf["violation_pattern"])
        if pnid not in seen_nodes:
            nodes.append(get_violation_pattern_node(vf["violation_pattern"]))
            seen_nodes.add(pnid)
        # Path → Pattern edge
        peid = make_edge_id(path_node_id, pnid, "HAS_VIOLATION")
        if peid not in seen_edges:
            edges.append({"id": peid, "source": path_node_id, "target": pnid, "type": "HAS_VIOLATION",
                          "properties": {"violation_index": vf.get("violation_index")}})
            seen_edges.add(peid)

        # PathSegments for suspicious triple
        idx = vf.get("violation_index", 0)
        if idx + 2 <= len(path):
            seg_asns = path[max(0, idx - 1) : idx + 2]
            if len(seg_asns) >= 3:
                sid = make_segment_id(seg_asns)
                if sid not in seen_nodes:
                    nodes.append({
                        "id": sid, "type": "PathSegment",
                        "label": "-".join(seg_asns),
                        "properties": {
                            "asns": seg_asns,
                            "relationship_pattern": vf.get("violation_pattern", ""),
                            "is_suspicious": True,
                            "candidate_middle_asn": seg_asns[1],
                        },
                    })
                    seen_nodes.add(sid)
                seid = make_edge_id(path_node_id, sid, "HAS_SEGMENT")
                if seid not in seen_edges:
                    edges.append({"id": seid, "source": path_node_id, "target": sid, "type": "HAS_SEGMENT", "properties": {}})
                    seen_edges.add(seid)
                meid = make_edge_id(sid, make_asn_id(seg_asns[1]), "MIDDLE_ASN")
                if meid not in seen_edges:
                    edges.append({"id": meid, "source": sid, "target": make_asn_id(seg_asns[1]), "type": "MIDDLE_ASN", "properties": {}})
                    seen_edges.add(meid)
                if pnid:
                    mpeid = make_edge_id(sid, pnid, "MATCHES_PATTERN")
                    if mpeid not in seen_edges:
                        edges.append({"id": mpeid, "source": sid, "target": pnid, "type": "MATCHES_PATTERN", "properties": {}})
                        seen_edges.add(mpeid)

    return _wrap(nodes, edges, {
        "is_valley_free": vf.get("is_valid"),
        "risk_score": risk.get("score", 0),
        "candidate_leaker": leak.get("candidate_asn"),
    })


# ---- ASN neighborhood subgraph ----

def build_asn_neighborhood_graph(
    asn: str,
    asrel=None,
    as2org=None,
    depth: int = 1,
    limit: int = 50,
    rel_filter: str = "all",
    include_org: bool = True,
    asrank: dict | None = None,
) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[str] = set()

    # Center node
    center = get_asn_node(asn, as2org, asrank)
    nodes.append(center)
    seen_nodes.add(make_asn_id(asn))

    # Org of center
    center_info = as2org.asn_to_org.get(asn) if as2org else None
    org_id = center_info.org_id if center_info else None
    if include_org and org_id:
        oid = make_org_id(org_id)
        if oid not in seen_nodes:
            nodes.append(get_org_node(org_id, as2org))
            seen_nodes.add(oid)
        eid = make_edge_id(make_asn_id(asn), oid, "BELONGS_TO")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": make_asn_id(asn), "target": oid, "type": "BELONGS_TO", "properties": {}})
            seen_edges.add(eid)

    # Country of center
    country = center_info.country if center_info else None
    if country:
        cid = make_country_id(country)
        if cid not in seen_nodes:
            nodes.append(get_country_node(country, as2org))
            seen_nodes.add(cid)
        eid = make_edge_id(make_asn_id(asn), cid, "LOCATED_IN")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": make_asn_id(asn), "target": cid, "type": "LOCATED_IN", "properties": {}})
            seen_edges.add(eid)

    # Neighbors
    nbr_data = get_asn_neighbors(asn, asrel, as2org, depth=1, limit=limit, rel_filter=rel_filter)
    rel_type_map = {"p2c": "P2C", "c2p": "C2P", "p2p": "P2P", "unknown": "UNKNOWN_REL", "same-org": "SAME_ORG_AS"}

    for entry in nbr_data["selected"]:
        p_asn = entry["asn"]
        rel = entry["relationship"]
        p_nid = make_asn_id(p_asn)
        if p_nid not in seen_nodes:
            nodes.append(get_asn_node(p_asn, as2org))
            seen_nodes.add(p_nid)

        etype = rel_type_map.get(rel, "UNKNOWN_REL")
        eid = make_edge_id(make_asn_id(asn), p_nid, etype)
        if eid not in seen_edges:
            edges.append({
                "id": eid, "source": make_asn_id(asn), "target": p_nid,
                "type": etype,
                "properties": {"relationship": rel, "same_org": rel == "same-org"},
            })
            seen_edges.add(eid)

        # Org + country for neighbor
        if include_org:
            n_info = as2org.asn_to_org.get(p_asn) if as2org else None
            n_org = n_info.org_id if n_info else None
            if n_org:
                oid = make_org_id(n_org)
                if oid not in seen_nodes:
                    nodes.append(get_org_node(n_org, as2org))
                    seen_nodes.add(oid)
                beid = make_edge_id(p_nid, oid, "BELONGS_TO")
                if beid not in seen_edges:
                    edges.append({"id": beid, "source": p_nid, "target": oid, "type": "BELONGS_TO", "properties": {}})
                    seen_edges.add(beid)

    # Same-org edges
    for sa in nbr_data["same_org"][:limit]:
        sa_nid = make_asn_id(sa)
        if sa_nid not in seen_nodes:
            nodes.append(get_asn_node(sa, as2org))
            seen_nodes.add(sa_nid)
        eid = make_edge_id(make_asn_id(asn), sa_nid, "SAME_ORG_AS")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": make_asn_id(asn), "target": sa_nid, "type": "SAME_ORG_AS",
                          "properties": {"relationship": "same-org", "same_org": True}})
            seen_edges.add(eid)

    warning = ""
    if nbr_data["total_neighbors"] > limit:
        warning = (
            f"This ASN has {nbr_data['total_neighbors']} neighbors. "
            f"Graph limited to top {limit}. Use filters to narrow the view."
        )

    return _wrap(nodes, edges, {
        "center_asn": asn,
        "summary": {
            "provider_count": len(nbr_data["providers"]),
            "peer_count": len(nbr_data["peers"]),
            "customer_count": len(nbr_data["customers"]),
            "same_org_asn_count": len(nbr_data["same_org"]),
            "unknown_count": len(nbr_data["unknowns"]),
            "shown_neighbors": len(nodes) - 1,  # minus center
            "total_neighbors": nbr_data["total_neighbors"],
            "depth": depth,
        },
        "warning": warning,
    })


# ---- Organization subgraph ----

def build_org_subgraph(org_id_or_name: str, asrel=None, as2org=None, limit: int = 100) -> dict:
    # Resolve org_id
    org_id = org_id_or_name
    if org_id not in (as2org.org_meta if as2org else {}):
        found = find_org_by_name(org_id_or_name, as2org)
        if found:
            org_id = found
        else:
            return _wrap([], [], {"error": f"Organization '{org_id_or_name}' not found"})

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[str] = set()

    # Org node
    nodes.append(get_org_node(org_id, as2org))
    seen_nodes.add(make_org_id(org_id))

    # Country
    meta = as2org.org_meta.get(org_id, {})
    country = meta.get("country", "")
    if country:
        cid = make_country_id(country)
        if cid not in seen_nodes:
            nodes.append(get_country_node(country, as2org))
            seen_nodes.add(cid)
        eid = make_edge_id(make_org_id(org_id), cid, "LOCATED_IN")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": make_org_id(org_id), "target": cid, "type": "LOCATED_IN", "properties": {}})
            seen_edges.add(eid)

    # Member ASNs
    members = as2org.org_to_asns.get(org_id, [])
    for asn in members[:limit]:
        nid = make_asn_id(asn)
        if nid not in seen_nodes:
            nodes.append(get_asn_node(asn, as2org))
            seen_nodes.add(nid)
        eid = make_edge_id(nid, make_org_id(org_id), "BELONGS_TO")
        if eid not in seen_edges:
            edges.append({"id": eid, "source": nid, "target": make_org_id(org_id), "type": "BELONGS_TO", "properties": {}})
            seen_edges.add(eid)

    # Internal edges (same-org)
    member_set = set(members)
    for (a, b), rel in (asrel.relationship_map if asrel else {}).items():
        if a in member_set and b in member_set:
            eid = make_edge_id(make_asn_id(a), make_asn_id(b), "SAME_ORG_AS")
            if eid not in seen_edges:
                edges.append({"id": eid, "source": make_asn_id(a), "target": make_asn_id(b), "type": "SAME_ORG_AS",
                              "properties": {"relationship": rel, "same_org": True}})
                seen_edges.add(eid)

    # External org neighbors
    ext_orgs = get_external_org_neighbors(org_id, asrel, as2org, limit=20)
    for ext in ext_orgs:
        eoid = make_org_id(ext["org_id"])
        if eoid not in seen_nodes:
            nodes.append(get_org_node(ext["org_id"], as2org))
            seen_nodes.add(eoid)
        # Aggregate edge
        dominant = "p2c" if ext["p2c"] >= ext["p2p"] and ext["p2c"] >= ext["c2p"] else (
            "p2p" if ext["p2p"] >= ext["c2p"] else "c2p"
        )
        rel_map = {"p2c": "P2C", "c2p": "C2P", "p2p": "P2P"}
        eid = make_edge_id(make_org_id(org_id), eoid, f"EXT_{rel_map.get(dominant, 'UNKNOWN')}")
        if eid not in seen_edges:
            edges.append({
                "id": eid, "source": make_org_id(org_id), "target": eoid,
                "type": f"EXT_{rel_map.get(dominant, 'UNKNOWN')}",
                "properties": {
                    "p2c_count": ext["p2c"], "p2p_count": ext["p2p"], "c2p_count": ext["c2p"],
                    "dominant_relationship": dominant,
                },
            })
            seen_edges.add(eid)

    return _wrap(nodes, edges, {
        "org_id": org_id,
        "org_name": meta.get("org_name", ""),
        "member_count": len(members),
        "external_org_count": len(ext_orgs),
    })


# ---- Violation pattern subgraph ----

def build_violation_pattern_graph(pattern: str, batch_export_rows: list[dict] | None = None) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[str] = set()

    pnid = make_pattern_id(pattern)
    nodes.append(get_violation_pattern_node(pattern))
    seen_nodes.add(pnid)

    matched_count = 0
    for row in (batch_export_rows or []):
        seq_str = row.get("relationship_sequence", "")
        seq = [s.strip() for s in seq_str.split("->")] if seq_str else []
        for i in range(len(seq) - 1):
            if f"{seq[i]} -> {seq[i+1]}" == pattern:
                matched_count += 1
                path_str = row.get("normalized_path", "")
                path = path_str.split()
                leaker = row.get("candidate_leaker_asn", "")
                if leaker:
                    lnid = make_asn_id(leaker)
                    if lnid not in seen_nodes:
                        nodes.append({"id": lnid, "type": "ASN", "label": f"AS{leaker}",
                                      "properties": {"asn": leaker, "is_candidate_for_pattern": True}})
                        seen_nodes.add(lnid)
                    eid = make_edge_id(pnid, lnid, "CANDIDATE_ASN")
                    if eid not in seen_edges:
                        edges.append({"id": eid, "source": pnid, "target": lnid, "type": "CANDIDATE_ASN", "properties": {"count": 1}})
                        seen_edges.add(eid)
                break

    return _wrap(nodes, edges, {"pattern": pattern, "matched_paths": matched_count})