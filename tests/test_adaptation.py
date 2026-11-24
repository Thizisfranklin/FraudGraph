import numpy as np
import pandas as pd
import pytest
from fraudgraph.adaptation import eligible_training, Specification


@pytest.fixture
def history():
    return pd.DataFrame({
        "Time step": list(range(1, 50)),
        "y": [i % 2 for i in range(1, 50)],
        "amount": list(range(1, 50)),
    })


def test_expanding_never_sees_current_or_delayed_labels(history):
    train, weights, cutoff = eligible_training(history, 40, "expanding", label_lag=2)
    assert cutoff == 38
    assert train["Time step"].max() == 38
    assert len(weights) == len(train)


def test_rolling_window_boundaries(history):
    train, _, cutoff = eligible_training(history, 40, "rolling", label_lag=2, rolling_steps=15)
    assert cutoff == 38
    assert train["Time step"].min() == 24
    assert train["Time step"].max() == 38


def test_recency_weights_increase_toward_latest(history):
    train, weights, cutoff = eligible_training(history, 40, "recency", label_lag=2)
    assert cutoff == 38
    assert weights[-1] > weights[0]
    assert weights[-1] == 1.


def test_frozen_uses_29_only_and_rejects_unavailable_labels(history):
    train, _, cutoff = eligible_training(history, 40, "frozen", label_lag=2)
    assert cutoff == train["Time step"].max() == 29
    with pytest.raises(ValueError, match="unavailable"):
        eligible_training(history, 30, "frozen", label_lag=2)


def test_unknowns_cannot_enter_training(history):
    history.loc[history["Time step"] == 25, "y"] = np.nan
    train, _, _ = eligible_training(history, 40, "expanding", label_lag=2)
    assert train.y.notna().all()
    assert 25 not in train["Time step"].to_list()


def test_specs_produce_stable_identifiers():
    assert Specification("rolling", 3, 150).name == "rolling_depth3_trees150_lr0.05"
