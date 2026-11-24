import numpy as np
import pandas as pd
import pytest

from fraudgraph.robustness import (
    CAPACITY_PRESETS, analyst_capacity, choose_by_validation,
    known_average_precision, one_forward_fold,
    validation_backtest,
)


def test_capacity_uses_all_traffic_and_unknowns_consume_slots():
    bucket = pd.DataFrame({
        "txId": [9, 5, 2, 3, 4],
        "y": [1., 0., np.nan, 1., 0.],
    })
    rows = analyst_capacity(bucket, [.7, .1, .99, .6, .2], fractions=(.2, .4))
    assert rows[0]["reviewed"] == 1
    assert rows[0]["known_illicit"] == 0
    assert rows[0]["unknown"] == 1
    assert rows[0]["known_illicit_capture"] == 0.
    assert rows[1]["known_illicit"] == 1
    assert rows[1]["unknown"] == 1
    assert rows[1]["known_illicit_capture"] == .5
    assert rows[1]["precision_lower_bound"] == .5
    assert rows[1]["precision_upper_bound"] == 1.


def test_capacity_validates_scores_and_duplicates():
    f = pd.DataFrame({"txId": [1, 1], "y": [1., 0.]})
    with pytest.raises(ValueError, match="duplicate"):
        analyst_capacity(f, [.7, .8])
    f.loc[1, "txId"] = 2
    with pytest.raises(ValueError, match="finite"):
        analyst_capacity(f, [.7, np.nan])


def test_one_class_ap_is_undefined():
    assert np.isnan(known_average_precision([0, 0], [.1, .4]))
    assert known_average_precision([0, 1], [.1, .8]) == 1.


@pytest.fixture
def history():
    rng = np.random.default_rng(42)
    rows = []
    for t in range(1, 50):
        for i in range(14):
            label = float(i % 2) if i != 13 else np.nan
            rows.append({"txId": 100 * t + i, "Time step": t,
                         "y": label, "feat": float(i) + .1 * rng.normal()})
    return pd.DataFrame(rows)


def test_forward_fold_keeps_unknown_labels_out_and_uses_lag(history):
    outcome, capacity = one_forward_fold(
        history, ["feat"], 40, "expanding",
        CAPACITY_PRESETS[0], label_lag=4,
    )
    assert outcome["last_labeled_training_step"] == 36
    assert outcome["evaluated_labeled"] == 13
    assert outcome["trained_labeled"] == 36 * 13
    assert np.isfinite(outcome["train_ap_in_sample"])
    assert np.isfinite(outcome["forward_ap"])
    assert len(capacity) == 3
    assert capacity[0]["reviewed"] == 1


def test_validation_selection_prioritizes_worst_period_then_mean():
    folds = pd.DataFrame([
        {"label_lag": 2, "candidate": "frozen__low_capacity",
         "strategy": "frozen", "capacity_preset": "low_capacity",
         "forward_ap": x, "forward_ap_above_prevalence": x-.1,
         "excess_ap_gap": .05}
        for x in [.8, .8, .2]
    ] + [
        {"label_lag": 2, "candidate": "expanding__regularized",
         "strategy": "expanding", "capacity_preset": "regularized",
         "forward_ap": x, "forward_ap_above_prevalence": x-.1,
         "excess_ap_gap": .05}
        for x in [.55, .5, .5]
    ])
    _, chosen = choose_by_validation(folds)
    assert chosen.iloc[0].candidate == "expanding__regularized"


def test_validation_guard_requires_old_labels_mature():
    minimal = pd.DataFrame({"Time step": [1, 2], "y": [0., 1.]})
    with pytest.raises(ValueError, match="frozen training"):
        validation_backtest(minimal, ["y"], steps=(32, 33), label_lags=(6,))
