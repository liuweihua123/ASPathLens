"""Typer CLI — full commands for Phase 3."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.database import init_db
from app.services.batch_analyzer import BatchRow, parse_batch_csv, parse_batch_txt, run_batch, export_batch_csv
from app.services.dataset_status import get_dataset_status
from app.services.report_exporter import generate_markdown_report
from app.services.path_diff import diff_paths
from app.services.path_normalizer import normalize_as_path
from app.state import data_store

app = typer.Typer(name="aspathlens", help="AS path policy analysis CLI")
console = Console()


def _ensure_data():
    init_db()
    data_store.reload_from_disk()


# ---- analyze ----
@app.command()
def analyze(
    as_path: str = typer.Argument(..., help="AS path, e.g. '3356 4134 4837 9808'"),
    format: str = typer.Option("table", "--format", "-f", help="table|json|markdown"),
):
    """Analyze a single AS path."""
    _ensure_data()
    result = data_store.analyzer().analyze(as_path)
    if format == "json":
        console.print_json(json.dumps(result, ensure_ascii=False, default=str))
        return
    if format == "markdown":
        console.print(generate_markdown_report(result))
        return
    _print_result_table(result)


# ---- diff ----
@app.command()
def diff(
    before: str = typer.Argument(..., help="Before path"),
    after: str = typer.Argument(..., help="After path"),
    format: str = typer.Option("table", "--format", "-f", help="table|json|markdown"),
):
    """Compare two AS paths."""
    _ensure_data()
    out = diff_paths(data_store.analyzer(), before, after)
    if format == "json":
        console.print_json(json.dumps(out, ensure_ascii=False, default=str))
        return
    d = out["diff"]
    t = Table(title="ASPathLens Path Diff")
    t.add_column("Field")
    t.add_column("Value")
    t.add_row("Before", " -> ".join(out["before"]["path"]))
    t.add_row("After", " -> ".join(out["after"]["path"]))
    t.add_row("Before risk", f'{out["before"]["risk_score"]} ({out["before"]["level"]})')
    t.add_row("After risk", f'{out["after"]["risk_score"]} ({out["after"]["level"]})')
    t.add_row("Risk delta", str(d["risk_delta"]))
    t.add_row("Added ASNs", ", ".join(d["added_asns"]) or "—")
    t.add_row("Removed ASNs", ", ".join(d["removed_asns"]) or "—")
    if d.get("relationship_changes"):
        t.add_row("Rel changes", str(len(d["relationship_changes"])))
    console.print(t)
    console.print(f"\n{d.get('interpretation_en', '')}")
    console.print(f"[dim]{d.get('interpretation_zh', '')}[/dim]")


# ---- batch ----
@app.command()
def batch(
    file: str = typer.Argument(..., help="CSV or TXT file"),
    output: str = typer.Option("", "--output", "-o", help="Output file (CSV/JSON)"),
    format: str = typer.Option("table", "--format", "-f", help="table|json|csv"),
):
    """Batch analyze AS paths from file."""
    _ensure_data()
    path = Path(file)
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".csv":
        rows = parse_batch_csv(text)
    else:
        rows = parse_batch_txt(text)

    console.print(f"Loaded {len(rows)} paths")
    result = run_batch(data_store.analyzer(), rows)

    if format == "json" or (output and output.endswith(".json")):
        out = json.dumps(result["export_rows"], indent=2, ensure_ascii=False)
    elif format == "csv" or (output and output.endswith(".csv")):
        out = export_batch_csv(result["export_rows"])
    else:
        _print_batch_table(result)
        return

    if output:
        Path(output).write_text(out, encoding="utf-8")
        console.print(f"Saved to {output}")
    else:
        console.print(out)


# ---- asn ----
@app.command()
def asn(asn_id: str = typer.Argument(..., help="ASN to explore")):
    """Explore an ASN profile."""
    _ensure_data()
    store = data_store.as2org
    rel = data_store.asrel
    asn_id = asn_id.upper().replace("AS", "").strip()
    info = store.asn_to_org.get(asn_id) if store else None
    t = Table(title=f"AS{asn_id}")
    t.add_column("Field")
    t.add_column("Value")
    if info:
        t.add_row("Org name", info.org_name or "—")
        t.add_row("AS name", info.as_name or "—")
        t.add_row("Country", info.country or "—")
        t.add_row("Org ID", info.org_id or "—")
        same = [a for a in (store.org_to_asns.get(info.org_id, []) if store else []) if a != asn_id]
        t.add_row("Same-org ASNs", ", ".join(same[:10]) + ("..." if len(same) > 10 else ""))
    else:
        t.add_row("Status", "Not in AS2Org data")
    if rel:
        providers = peers = customers = 0
        for (a, b), r in rel.relationship_map.items():
            if a != asn_id:
                continue
            if r == "c2p": providers += 1
            elif r == "p2p": peers += 1
            elif r == "p2c": customers += 1
        t.add_row("Providers", str(providers))
        t.add_row("Peers", str(peers))
        t.add_row("Customers", str(customers))
    console.print(t)


# ---- dataset ----
dataset_app = typer.Typer(name="dataset", help="Dataset management")
app.add_typer(dataset_app, name="dataset")


@dataset_app.command("status")
def dataset_status():
    """Show dataset status."""
    _ensure_data()
    status = get_dataset_status(asrel=data_store.asrel, as2org=data_store.as2org)
    t = Table(title="Dataset Status")
    t.add_column("Dataset")
    t.add_column("Status")
    t.add_column("Details")
    rel = status.get("as_relationship", {})
    t.add_row("AS Relationship", rel.get("status", "?"), f"edges: {rel.get('loaded_edge_count', '?')}")
    org = status.get("as2org", {})
    t.add_row("AS2Org", org.get("status", "?"), f"ASNs: {org.get('loaded_asn_count', '?')}, orgs: {org.get('org_count', '?')}")
    api = status.get("asrank_api", {})
    t.add_row("ASRank API", api.get("status", "?"), api.get("message", ""))
    console.print(t)


@dataset_app.command("diff")
def dataset_diff_cmd(
    dataset: str = typer.Option("as_relationship", "--dataset", "-d"),
    old: str = typer.Option(..., "--old", help="Old version date"),
    new: str = typer.Option(..., "--new", help="New version date"),
    format: str = typer.Option("table", "--format", "-f"),
):
    """Compare two dataset versions."""
    from app.api.dataset_diff_api import dataset_diff
    try:
        result = dataset_diff(dataset, old, new)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
    if format == "json":
        console.print_json(json.dumps(result, default=str))
        return
    t = Table(title=f"Dataset Diff: {dataset}")
    t.add_column("Field")
    t.add_column("Value")
    for k, v in result.items():
        if not isinstance(v, (dict, list)):
            t.add_row(str(k), str(v))
    console.print(t)


# ---- helpers ----
def _print_result_table(result: dict):
    t = Table(title="ASPathLens Analyze")
    t.add_column("Field")
    t.add_column("Value")
    t.add_row("Path", " -> ".join(result.get("normalized_path", [])))
    t.add_row("Org path", " -> ".join(result.get("org_path", [])))
    t.add_row("Sequence", " -> ".join(result.get("relationship_sequence", [])))
    vf = result.get("valley_free", {})
    t.add_row("Valley-free", str(vf.get("is_valid")))
    if vf.get("violation_pattern"):
        t.add_row("Violation", vf["violation_pattern"])
    leak = result.get("route_leak_candidate", {})
    if leak.get("is_candidate"):
        t.add_row("Leak candidate", f"AS{leak.get('candidate_asn')} ({leak.get('confidence')})")
    risk = result.get("risk_score", {})
    t.add_row("Risk", f"{risk.get('score')} ({risk.get('level')})")
    for e in risk.get("evidence", []):
        t.add_row("  Evidence", e)
    console.print(t)


def _print_batch_table(result: dict):
    console.print(f"\nTotal: {result['total_paths']} | "
                  f"Valley-free: {result['valley_free_valid_count']} | "
                  f"Suspicious: {result['suspicious_count']} | "
                  f"Unknown-heavy: {result['unknown_heavy_count']}\n")
    if result.get("top_violation_patterns"):
        t = Table(title="Top violation patterns")
        t.add_column("Pattern")
        t.add_column("Count", justify="right")
        for p in result["top_violation_patterns"][:10]:
            t.add_row(p["pattern"], str(p["count"]))
        console.print(t)
    t = Table(title="Per-path results")
    t.add_column("ID")
    t.add_column("Path", max_width=30)
    t.add_column("Sequence", max_width=20)
    t.add_column("VF")
    t.add_column("Risk")
    t.add_column("Level")
    for row in result.get("export_rows", []):
        t.add_row(
            row["path_id"],
            row["normalized_path"],
            row["relationship_sequence"],
            str(row.get("is_valley_free")),
            str(row["risk_score"]),
            row["risk_level"],
        )
    console.print(t)


if __name__ == "__main__":
    app()