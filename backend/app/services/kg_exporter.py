"""Knowledge Graph exporter — JSON, Cytoscape JSON, GraphML, Cypher."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET


def export_json(graph: dict) -> dict:
    """Return raw JSON graph."""
    return graph


def export_cytoscape(graph: dict) -> dict:
    """Convert to Cytoscape.js compatible format."""
    cy_nodes = []
    for n in graph.get("nodes", []):
        cy_nodes.append({"data": {**n.get("properties", {}), "id": n["id"], "label": n.get("label", n["id"]), "type": n["type"]}})
    cy_edges = []
    for e in graph.get("edges", []):
        cy_edges.append({"data": {**e.get("properties", {}), "id": e["id"], "source": e["source"], "target": e["target"], "type": e.get("type", "")}})
    return {"elements": {"nodes": cy_nodes, "edges": cy_edges}, "meta": graph.get("meta", {})}


def export_graphml(graph: dict) -> str:
    """Export to GraphML XML string."""
    root = ET.Element("graphml", xmlns="http://graphml.graphstruct.org/graphml")
    # Key definitions
    for attr in ["type", "label", "relationship", "same_org", "is_violation_edge", "is_candidate_leaker"]:
        k = ET.SubElement(root, "key")
        k.set("id", attr)
        k.set("for", "node" if attr in ("type", "label") else "edge")
        k.set("attr.name", attr)
        k.set("attr.type", "string")

    graph_el = ET.SubElement(root, "graph", edgedefault="directed")
    for n in graph.get("nodes", []):
        node_el = ET.SubElement(graph_el, "node", id=n["id"])
        d1 = ET.SubElement(node_el, "data", key="type"); d1.text = n.get("type", "")
        d2 = ET.SubElement(node_el, "data", key="label"); d2.text = n.get("label", "")
    for e in graph.get("edges", []):
        edge_el = ET.SubElement(graph_el, "edge", id=e["id"], source=e["source"], target=e["target"])
        d1 = ET.SubElement(edge_el, "data", key="type"); d1.text = e.get("type", "")
        props = e.get("properties", {})
        if "relationship" in props:
            d2 = ET.SubElement(edge_el, "data", key="relationship"); d2.text = str(props["relationship"])

    buf = io.StringIO()
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(buf, encoding="unicode", xml_declaration=True)
    return buf.getvalue()


def export_cypher(graph: dict) -> str:
    """Export to Cypher MERGE statements (for optional Neo4j import)."""
    lines: list[str] = []

    for n in graph.get("nodes", []):
        props = n.get("properties", {}).copy()
        props["label"] = n.get("label", "")
        props_str = ", ".join(f'{k}: "{v}"' for k, v in props.items() if v is not None and v != "")
        ntype = n["type"].replace(" ", "_")
        lines.append(f'MERGE (n:{ntype} {{id: "{n["id"]}", {props_str}}})')

    for e in graph.get("edges", []):
        props = e.get("properties", {}).copy()
        props_str = ", ".join(f'{k}: "{v}"' for k, v in props.items() if v is not None and v != "")
        etype = e.get("type", "RELATED_TO").replace(" ", "_")
        prop_block = f" {{{props_str}}}" if props_str else ""
        lines.append(f'MERGE (a {{id: "{e["source"]}"}})')
        lines.append(f'MERGE (b {{id: "{e["target"]}"}})')
        lines.append(f'MERGE (a)-[:{etype}{prop_block}]->(b)')

    return ";\n".join(lines) + ";" if lines else ""