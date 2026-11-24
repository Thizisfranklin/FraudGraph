import numpy as np
import pandas as pd
from fraudgraph.drift import population_stability_index, feature_shift, score_and_label_summary


def test_psi_identical_vs_changed_and_missing():
    base = np.arange(100, dtype=float)
    assert abs(population_stability_index(base, base)) < 1e-12
    assert population_stability_index(base, base + 1000) > 0.5
    a = np.r_[base, np.nan]
    b = np.r_[base, [500]]
    assert np.isfinite(population_stability_index(a, b))


def test_feature_shift_checks_missing_rate_without_labels():
    a = pd.DataFrame({"amount": [1., 2., np.nan]})
    b = pd.DataFrame({"amount": [3., 4., 5.]})
    r = feature_shift(a, b, ["amount"], 43)[0]
    assert r["current_missing_rate"] == 0.
    assert np.isclose(r["reference_missing_rate"], 1 / 3)
    assert r["time_step"] == 43


def test_drift_summary_excludes_unknown_from_prevalence_and_ap():
    f = pd.DataFrame({
        "Time step": [40, 40, 40, 43, 43],
        "y": [1., 0., np.nan, 0., np.nan],
        "score": [.9, .1, .99, .9, .8],
    })
    result = score_and_label_summary(f, "score").set_index("time_step")
    assert result.loc[40, "known_illicit_prevalence"] == .5
    assert result.loc[40, "average_precision_labeled"] == 1.
    assert result.loc[40, "unknown"] == 1
    assert np.isnan(result.loc[43, "average_precision_labeled"])
