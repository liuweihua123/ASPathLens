import pytest

from app.services.path_normalizer import normalize_as_path
from app.services.valley_free import check_valley_free
from app.services.asrel_loader import parse_asrel_file
from app.services.risk_score import compute_coverage, compute_risk_score
from app.services.route_leak_patterns import detect_route_leak_pattern
from app.services.path_analyzer import AnalyzerContext, PathAnalyzerService
from app.services.as2org_loader import parse_as2org_file
from pathlib import Path
import tempfile
import textwrap


def test_normalizer_prepend_and_private():
    r = normalize_as_path("3356 4134 4134 4837")
    assert r.normalized_path == ["3356", "4134", "4837"]
    assert r.prepending_detected
    r2 = normalize_as_path("64512 64513")
    assert any("Private" in w for w in r2.warnings)


def test_normalizer_empty_invalid():
    r = normalize_as_path("  ")
    assert not r.normalized_path
    r2 = normalize_as_path("abc def")
    assert any("Invalid" in w for w in r2.warnings)


def test_asrel_parse(tmp_path):
    f = tmp_path / "test.as-rel2.txt"
    f.write_text(textwrap.dedent("""\
        # comment
        1|2|-1
        3|4|0|src
    """))
    store = parse_asrel_file(f)
    assert store.get_relationship("1", "2") == "p2c"
    assert store.get_relationship("2", "1") == "c2p"
    assert store.get_relationship("3", "4") == "p2p"


def test_valley_free_valid():
    vf = check_valley_free(["c2p", "p2p", "p2c"])
    assert vf.is_valid is True


def test_valley_free_violation_p2c_then_c2p():
    vf = check_valley_free(["p2c", "c2p"])
    assert vf.is_valid is False
    assert vf.violation_index == 1


def test_valley_free_unknown_all():
    vf = check_valley_free(["unknown", "unknown"])
    assert vf.uncertain


def test_route_leak_p2p_c2p():
    path = ["1", "2", "3"]
    seq = ["p2p", "c2p"]
    leak = detect_route_leak_pattern(path, seq, [False, False])
    assert leak.is_candidate
    assert leak.candidate_asn == "2"


def test_risk_score_violation():
    from app.services.valley_free import ValleyFreeOutput
    from app.services.route_leak_patterns import LeakPatternResult

    vf = ValleyFreeOutput(False, 1, "p2c -> c2p", "", "")
    leak = LeakPatternResult(True, "2", "p2c -> c2p", "high", "", "")
    cov = compute_coverage(["p2c", "c2p"], 1)
    risk = compute_risk_score(vf, leak, False, cov.known_ratio, 3, False)
    assert risk["score"] >= 60


def test_path_analyzer_minimal(tmp_path):
    rel = tmp_path / "r.txt"
    rel.write_text("100|200|-1\n200|300|0|x\n")
    org = tmp_path / "o.txt"
    org.write_text(textwrap.dedent("""\
        100|t|AS100|ORG1|x|s
        200|t|AS200|ORG1|x|s
        300|t|AS300|ORG2|x|s
        ORG1|t|Org One|US|s
        ORG2|t|Org Two|CN|s
    """))
    asrel = parse_asrel_file(rel)
    as2org = parse_as2org_file(org)
    svc = PathAnalyzerService(AnalyzerContext(asrel=asrel, as2org=as2org))
    out = svc.analyze("100 200 300")
    assert len(out["relationship_sequence"]) == 2
    assert out["risk_score"]["disclaimer"]