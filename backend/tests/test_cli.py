import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from trust_score import cli
from trust_score.models import Review

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent
END = date(2026, 6, 30)


def _reviews(spec):
    out = []
    for count, stars, text in spec:
        for _ in range(count):
            i = len(out)
            out.append(Review(f"r{i}", stars, END - timedelta(days=i), text, f"u{i}"))
    return out


def test_build_writes_valid_data_json(tmp_path):
    out = tmp_path / "data.json"
    args = cli.parser().parse_args(["build", "--out", str(out)])
    assert args.func(args) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert [(s["id"], s["band"], s["alert"] is not None) for s in doc["sellers"]] == [
        ("A", "High", False), ("B", "Medium", False), ("C", "Low", False),
        ("D", "Not enough data", False), ("E", "Not enough data", True)]


def test_build_output_matches_committed_data_json(tmp_path):
    out = tmp_path / "data.json"
    args = cli.parser().parse_args(["build", "--out", str(out)])
    args.func(args)
    assert out.read_text(encoding="utf-8") == (REPO / "data.json").read_text(encoding="utf-8")


def test_validate_exit_codes(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    assert cli.cmd_validate(argparse.Namespace(path=REPO / "data.json")) == 0
    assert cli.cmd_validate(argparse.Namespace(path=bad)) == 1


def test_share_sensitivity_counts_only_listings_meeting_polar_gate():
    by_listing = {
        "high": _reviews([(6, 1, "Bad."), (14, 5, "Good.")]),    # 30%
        "mid": _reviews([(5, 1, "Bad."), (15, 5, "Good.")]),     # 25%
        "small": _reviews([(10, 1, "Bad."), (9, 5, "Good.")]),   # 19 polar: skipped
    }
    assert cli.share_sensitivity(by_listing) == {
        "listings_meeting_polar_gate": 2, "at_or_above_20pct": 2,
        "at_or_above_25pct": 2, "at_or_above_30pct": 1}


def test_reviews_outcome_routes():
    repeated = _reviews([(1, 1, "This is fake."), (1, 1, "Received a different model."), (28, 5, "Good.")])
    concentrated = _reviews([(3, 1, "This is fake."), (5, 1, "Bad."), (12, 5, "Good.")])
    assert cli.reviews_outcome("x", repeated) == ("warn", "repeated")
    assert cli.reviews_outcome("y", concentrated) == ("warn", "concentration")
    assert cli.reviews_outcome("z", _reviews([(20, 5, "Good.")])) == ("pass", None)


@pytest.mark.skipif(not cli.INDIAN_CSV.exists(), reason="raw dataset not downloaded (gitignored)")
def test_screen_reproduces_research_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "REPORTS", tmp_path)
    cli.cmd_screen(argparse.Namespace(csv=cli.INDIAN_CSV))
    summary = json.loads((tmp_path / "screen_indian_products.json").read_text())
    assert (summary["nonempty_reviews"], summary["asins"], summary["one_or_two_star_reviews"],
            summary["low_star_with_any_selected_wording"],
            summary["low_star_with_authenticity_or_mismatch_wording"]) == (1388, 145, 338, 77, 42)


def test_check_synthetic_passes_all_expectations(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "REPORTS", tmp_path)
    assert cli.cmd_check_synthetic(argparse.Namespace(dir=cli.SYNTHETIC_DIR)) == 0
    report = json.loads((tmp_path / "check_synthetic.json").read_text())
    assert report["failures"] == []
    assert report["reviews_factor_outcomes"]["copied_complaint_burst"] == {"warn/concentration": 10}
    assert report["reviews_factor_outcomes"]["context_trap_burst"] == {"pass/None": 10}
