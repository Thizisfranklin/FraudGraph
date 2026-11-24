"""Smoke-test the standalone HTML viewer without downloading blockchain data."""
from pathlib import Path
import runpy

import pandas as pd


def test_offline_research_report_from_minimal_outputs(tmp_path):
    out = tmp_path / "reports/exploratory"
    out.mkdir(parents=True)
    pd.DataFrame([
        {"capacity_preset": "regularized", "strategy": "expanding",
         "train_ap_in_sample": .81, "forward_ap": .61},
        {"capacity_preset": "low_capacity", "strategy": "frozen",
         "train_ap_in_sample": .67, "forward_ap": .52},
    ]).to_csv(out / "regularization_validation_folds.csv", index=False)
    pd.DataFrame([
        {"label_lag": 2, "candidate": "expanding__regularized",
         "mean_forward_ap": .61, "worst_forward_ap": .45},
        {"label_lag": 4, "candidate": "frozen__low_capacity",
         "mean_forward_ap": .55, "worst_forward_ap": .41},
    ]).to_csv(out / "regularization_selected_per_lag.csv", index=False)
    pd.DataFrame([
        {"label_lag": lag, "capacity_fraction": fraction,
         "known_illicit_capture": 2 * fraction}
        for lag in (2, 4)
        for fraction in (.01, .05, .10)
    ]).to_csv(out / "capacity_validation.csv", index=False)

    script = Path(__file__).resolve().parents[1] / "scripts/build_research_dashboard.py"
    builder = runpy.run_path(str(script))["make_dashboard"]
    result = builder(tmp_path)
    page = result.read_text(encoding="utf-8")
    assert "FraudGraph" in page
    assert "Model capacity" in page
    assert "Unknown" in page or "unknown" in page
    assert "Plotly" in page
    assert "NOT a real-time fraud" in page
