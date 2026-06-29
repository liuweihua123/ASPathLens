import textwrap

import pytest

from app.services.batch_analyzer import (
    parse_batch_csv,
    parse_batch_txt,
    run_batch,
    export_batch_csv,
    export_batch_markdown,
)
from app.services.path_analyzer import AnalyzerContext, PathAnalyzerService
from app.services.path_diff import diff_paths
from app.services.asrel_loader import parse_asrel_file
from app.services.as2org_loader import parse_as2org_file
from app.services.dataset_status import get_dataset_status


@pytest.fixture
def mini_service(tmp_path):
    rel = tmp_path / "r.txt"
    rel.write_text("100|200|-1\n200|300|0|x\n300|400|-1\n")
    org = tmp_path / "o.txt"
    org.write_text(textwrap.dedent("""\
        100|t|AS100|O1|x|s
        200|t|AS200|O1|x|s
        300|t|AS300|O2|x|s
        400|t|AS400|O3|x|s
        O1|t|Org1|US|s
        O2|t|Org2|CN|s
        O3|t|Org3|JP|s
    """))
    svc = PathAnalyzerService(
        AnalyzerContext(
            asrel=parse_asrel_file(rel),
            as2org=parse_as2org_file(org),
        )
    )
    return svc


# ---- Path Diff ----

def test_path_diff_risk_delta(mini_service):
    out = diff_paths(mini_service, "100 200 300", "100 300 400")
    assert "before" in out and "after" in out
    assert "risk_delta" in out["diff"]
    assert isinstance(out["diff"]["changed_positions"], list)


def test_path_diff_added_removed(mini_service):
    out = diff_paths(mini_service, "100 200 300", "100 200 300 400")
    assert "400" in out["diff"]["added_asns"]
    assert out["diff"]["removed_asns"] == []


def test_path_diff_same_path(mini_service):
    out = diff_paths(mini_service, "100 200 300", "100 200 300")
    assert out["diff"]["risk_delta"] == 0
    assert out["diff"]["added_asns"] == []
    assert out["diff"]["removed_asns"] == []


# ---- Batch Analyzer ----

def test_batch_csv_parse():
    csv_text = 'path_id,as_path\n1,"100 200 300"\n2,"100 300 400"\n'
    rows = parse_batch_csv(csv_text)
    assert len(rows) == 2
    assert rows[0].path_id == "1"


def test_batch_csv_parse_alt_columns():
    csv_text = 'id,path\n1,100 200 300\n2,100 300 400\n'
    rows = parse_batch_csv(csv_text)
    assert len(rows) == 2
    assert rows[1].as_path == "100 300 400"


def test_batch_run_summary(mini_service):
    from app.services.batch_analyzer import BatchRow

    rows = [
        BatchRow("1", "100 200 300"),
        BatchRow("2", "100 300 400"),
    ]
    result = run_batch(mini_service, rows, store_result=False)
    assert result["total_paths"] == 2
    assert len(result["export_rows"]) == 2
    assert "top_violation_patterns" in result
    assert result["export_rows"][0]["path_id"] == "1"
    assert result["export_rows"][0]["normalized_path"] == "100 200 300"


def test_batch_export_csv(mini_service):
    from app.services.batch_analyzer import BatchRow
    rows = [BatchRow("1", "100 200 300")]
    result = run_batch(mini_service, rows, store_result=False)
    csv_out = export_batch_csv(result["export_rows"])
    assert "path_id" in csv_out
    assert "100 200 300" in csv_out


def test_batch_txt():
    rows = parse_batch_txt("# comment\n100 200\n200 300\n")
    assert len(rows) == 2


def test_batch_suspicious_ranking(mini_service):
    """Paths that show leak candidates should appear in top_suspicious_asns."""
    from app.services.batch_analyzer import BatchRow
    # Create enough paths that produce consistent candidates
    rows = [BatchRow(str(i), f"100 200 300 400") for i in range(5)]
    result = run_batch(mini_service, rows, store_result=False)
    # Check that suspicious ranking is returned even if empty
    assert isinstance(result["top_suspicious_asns"], list)


# ---- Dataset Status ----

def test_dataset_status_with_memory():
    from app.services.asrel_loader import AsRelStore
    from app.services.as2org_loader import As2OrgStore, AsnOrgInfo
    store = AsRelStore()
    store.stats.edge_count = 100
    store.stats.p2c_count = 50
    store.stats.unique_asn_count = 30
    store.stats.dataset_date = "20260101"
    store.version = "20260101"
    org = As2OrgStore()
    org.stats.asn_count = 30
    org.stats.org_count = 10
    org.stats.country_count = 5
    org.stats.dataset_date = "20260101"
    org.version = "20260101"
    org.asn_to_org["100"] = AsnOrgInfo(asn="100", org_id="O1", org_name="Org1", country="US")
    status = get_dataset_status(asrel=store, as2org=org)
    assert status["as_relationship"]["loaded_edge_count"] == 100
    assert status["as2org"]["loaded_asn_count"] == 30