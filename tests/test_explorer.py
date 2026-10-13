"""Smoke checks for the saved-report explorer (no raw Elliptic++ data needed)."""
from pathlib import Path

import pytest

from explorer_data import (
    capacity_at, comparison_ids, exact_row, known_illicit_total,
    load_reports, test_ap, test_curve,
)


ROOT = Path(__file__).resolve().parents[1]


def test_load_committed_reports():
    tables = load_reports(ROOT / "reports")
    assert set(tables) == {"results", "review_capacity", "test_by_time", "cases"}
    assert len(tables["cases"]) == 3


def test_primary_model_average_precision():
    reports = load_reports(ROOT / "reports")
    baseline, graph = comparison_ids("named", "xgboost")
    assert test_ap(reports["results"], baseline) == pytest.approx(0.4239384)
    assert test_ap(reports["results"], graph) == pytest.approx(0.5239738)


def test_all_traffic_workload_reconciliation():
    reports = load_reports(ROOT / "reports")
    result = capacity_at(
        reports["review_capacity"], reports["test_by_time"],
        "named_xgboost_graph", 0.05,
    )
    assert result["reviewed"] == 2337
    assert result["known_illicit"] == 273
    assert result["known_licit"] == 140
    assert result["unknown"] == 1924
    assert result["total_known_illicit"] == 636
    assert result["known_illicit_recall"] == pytest.approx(273 / 636)


def test_budget_levels_are_saved_not_interpolated():
    reports = load_reports(ROOT / "reports")
    curve = test_curve(reports["review_capacity"], "named_xgboost_graph")
    assert list(curve["capacity_fraction"]) == [.01, .02, .05, .1, .2]
    with pytest.raises(ValueError, match="Expected one"):
        capacity_at(
            reports["review_capacity"], reports["test_by_time"],
            "named_xgboost_graph", 0.075,
        )


def test_invalid_or_missing_reports_rejected(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing committed report"):
        load_reports(tmp_path)
    with pytest.raises(ValueError, match="Unknown"):
        comparison_ids("invalid", "logistic")


def test_saved_time_buckets_are_not_duplicated():
    reports = load_reports(ROOT / "reports")
    total = known_illicit_total(reports["test_by_time"], "named_xgboost_graph")
    assert total == 636
