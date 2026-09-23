import numpy as np
import pandas as pd
from fraudgraph.evaluation import metrics, capacity_table, policy_thresholds, f1_threshold
from fraudgraph.pipeline import split_masks, sql_statements


def test_unknowns_consume_capacity():
    f = pd.DataFrame({"txId": [1, 2, 3, 4], "Time step": [1]*4,
                      "y": [np.nan, 1., 0., 0.], "score": [.99, .9, .4, .1]})
    c = capacity_table(f, "score", fractions=(.25,))
    all_ = c[c.scope == "all_transactions"].iloc[0]
    labeled = c[c.scope == "labeled_only"].iloc[0]
    assert all_.unknown == 1 and all_.known_licit == 0
    assert all_.recall_at_k_known == 0
    assert all_.precision_lower_bound_all == 0 and all_.precision_upper_bound_all == 1
    assert labeled.precision_at_k_known == 1


def test_tied_scores_deterministic_by_id():
    f = pd.DataFrame({"txId": [2, 1], "Time step": [1, 1], "y": [0., 1.], "score": [.5, .5]})
    c = capacity_table(f, "score", fractions=(.5,))
    assert (c.known_illicit == 1).all()


def test_high_disabled_when_precision_target_unattainable():
    low, high = policy_thresholds([0, 1], [.9, .8], [.9, .8], .5, .9, 2)
    assert np.isinf(high)


def test_high_threshold_does_not_split_ties():
    low, high = policy_thresholds([1, 0, 0], [.9, .9, .1], [.9, .9, .1], 1., .9, 1)
    assert np.isinf(high)


def test_temporal_boundaries_disjoint_and_complete():
    f = pd.DataFrame({"Time step": range(1, 50)})
    masks = split_masks(f, {"train_end": 29, "validation_end": 39})
    assert np.all(np.array(list(masks.values())).sum(axis=0) == 1)
    assert [m.sum() for m in masks.values()] == [29, 10, 10]


def test_confusion_matrix_and_threshold():
    m = metrics([0, 0, 1, 1], [.1, .7, .6, .9], .5)
    assert (m["tn"], m["fp"], m["fn"], m["tp"]) == (1, 1, 0, 2)
    assert m["false_positive_rate"] == .5
    assert f1_threshold([0, 0, 1, 1], [.1, .2, .8, .9]) == .8


def test_sql_comment_semicolons_preserved():
    import sqlite3
    statements = list(sql_statements("-- comment; continuation\nSELECT 'a;b';\nSELECT 2;\n"))
    assert len(statements) == 2
    with sqlite3.connect(":memory:") as connection:
        assert connection.execute(statements[0]).fetchone()[0] == "a;b"
