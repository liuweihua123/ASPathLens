"""Knowledge Graph tests."""

import textwrap
import pytest

from app.services.as2org_loader import parse_as2org_file
from app.services.asrel_loader import parse_asrel_file
from app.services.kg_builder import build_asn_neighborhood_graph, build_org_subgraph, build_path_subgraph
from app.services.kg_exporter import export_cytoscape, export_cypher, export_graphml, export_json
from app.services.kg_query import get_asn_node, get_asn_neighbors, get_violation_pattern_node
from app.services.path_analyzer import AnalyzerContext, PathAnalyzerService


@pytest.fixture
def mini(tmp_path):
    rel = tmp_path / "r.txt"
    # 100 is provider of 200 (100→200: p2c), 200 peers with 300, 300 is provider of 400
    rel.write_text("100|200|-1\n200|300|0|x\n300|400|-1\n400|500|0|x\n")
    org = tmp_path / "o.txt"
    org.write_text(textwrap.dedent("""\
        100|t|AS100|O1|x|s
        200|t|AS200|O2|x|s
        300|t|AS300|O2|x|s
        400|t|AS400|O3|x|s
        500|t|AS500|O3|x|s
        O1|t|Org1|US|s
        O2|t|Org2|CN|s
        O3|t|Org3|JP|s
    """))
    asrel = parse_asrel_file(rel)
    as2org = parse_as2org_file(org)
    svc = PathAnalyzerService(AnalyzerContext(asrel=asrel, as2org=as2org))
    return asrel, as2org, svc


def test_asn_node(mini):
    _, as2org, _ = mini
    n = get_asn_node("200", as2org)
    assert n["id"] == "asn:200"
    assert n["type"] == "ASN"
    assert n["properties"]["org_name"] == "Org2"


def test_asn_neighbors_classify(mini):
    """200→100: c2p (100 is provider), 200→300: p2p (peer), 200→400: c2p (provider).
    Relationship map has (200,100)=c2p, (200,300)=p2p, (200,400)=c2p.
    So providers=[100,400], peers=[300], customers=[] (no p2c from 200)."""
    asrel, as2org, _ = mini
    nbr = get_asn_neighbors("200", asrel, as2org)
    prov_asns = [e["asn"] for e in nbr["providers"]]
    assert "100" in prov_asns
    peer_asns = [e["asn"] for e in nbr["peers"]]
    assert "300" in peer_asns


def test_same_org(mini):
    """200 and 300 share org O2."""
    _, as2org, _ = mini
    nbr = get_asn_neighbors("200", None, as2org)
    assert "300" in nbr["same_org"]


def test_path_subgraph(mini):
    _, as2org, svc = mini
    result = svc.analyze("100 200 300 400")
    graph = build_path_subgraph(result, as2org=as2org)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "asn:100" in node_ids
    assert "asn:400" in node_ids
    edge_types = {e["type"] for e in graph["edges"]}
    assert "CONTAINS_ASN" in edge_types


def test_asn_neighborhood_graph(mini):
    asrel, as2org, _ = mini
    graph = build_asn_neighborhood_graph("200", asrel=asrel, as2org=as2org, limit=50)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "asn:200" in node_ids
    assert "asn:100" in node_ids  # provider
    assert "asn:300" in node_ids  # peer
    assert graph["meta"]["summary"]["provider_count"] >= 1
    assert graph["meta"]["summary"]["peer_count"] >= 1


def test_org_subgraph(mini):
    asrel, as2org, _ = mini
    graph = build_org_subgraph("O2", asrel=asrel, as2org=as2org)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "org:O2" in node_ids  # exact case
    assert "asn:200" in node_ids
    assert "asn:300" in node_ids


def test_org_subgraph_by_name(mini):
    asrel, as2org, _ = mini
    graph = build_org_subgraph("Org2", asrel=asrel, as2org=as2org)
    assert graph["meta"]["org_id"] == "O2"


def test_violation_pattern_node():
    n = get_violation_pattern_node("p2p -> c2p")
    assert n["type"] == "ViolationPattern"
    assert "p2p" in n["id"]


def test_cytoscape_export(mini):
    _, as2org, svc = mini
    result = svc.analyze("100 200 300 400")
    graph = build_path_subgraph(result, as2org=as2org)
    cy = export_cytoscape(graph)
    assert "elements" in cy
    assert len(cy["elements"]["nodes"]) > 0
    assert len(cy["elements"]["edges"]) > 0
    assert "id" in cy["elements"]["nodes"][0]["data"]


def test_graphml_export(mini):
    _, as2org, svc = mini
    result = svc.analyze("100 200 300 400")
    graph = build_path_subgraph(result, as2org=as2org)
    gml = export_graphml(graph)
    assert "<?xml" in gml
    assert "<graphml" in gml
    assert "asn:100" in gml


def test_cypher_export(mini):
    _, as2org, svc = mini
    result = svc.analyze("100 200 300 400")
    graph = build_path_subgraph(result, as2org=as2org)
    cypher = export_cypher(graph)
    assert "MERGE" in cypher
    assert "asn:100" in cypher


def test_asrank_unavailable(mini):
    """Graph should still build when ASRank returns nothing."""
    asrel, as2org, _ = mini
    graph = build_asn_neighborhood_graph("200", asrel=asrel, as2org=as2org, asrank={"available": False})
    assert len(graph["nodes"]) > 0
    assert graph["meta"]["center_asn"] == "200"


def test_depth2_limit(mini):
    asrel, as2org, _ = mini
    graph = build_asn_neighborhood_graph("200", asrel=asrel, as2org=as2org, depth=2, limit=5)
    assert len(graph["nodes"]) <= 15  # center + up to 5 neighbors + their orgs/countries


def test_large_asn_warning(mini):
    """When limit < total neighbors, a warning is returned."""
    asrel, as2org, _ = mini
    graph = build_asn_neighborhood_graph("200", asrel=asrel, as2org=as2org, limit=1)
    if graph["meta"]["summary"]["total_neighbors"] > 1:
        assert graph["meta"]["warning"] != ""