from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd
import pytest


def exporter():
    file = Path(__file__).resolve().parents[1] / "scripts/export_investigator_samples.py"
    spec = importlib.util.spec_from_file_location("fg_case_export", str(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_neighborhood_only_uses_nodes_visible_at_bucket_close():
    mod = exporter()
    nodes = pd.DataFrame({
        "txId": [10, 11, 12, 13, 14],
        "Time step": [1, 1, 2, 3, 1],
        "class": [1, 2, 3, 1, 3],
    })
    edges = pd.DataFrame({
        "txId1": [10, 10, 10, 11, 14],
        "txId2": [11, 12, 13, 10, 10],
    })
    snapshot = mod.neighborhood(10, nodes, edges)
    assert set(n["id"] for n in snapshot["nodes"]) == {"10", "11", "14"}
    assert {(e["source"], e["target"]) for e in snapshot["edges"]} == {
        ("10", "11"), ("11", "10"), ("14", "10")
    }
    assert all(n["timeStep"] <= 1 for n in snapshot["nodes"])


def test_neighborhood_bounds_neighbors_deterministically():
    mod = exporter()
    nodes = pd.DataFrame({
        "txId": [10, 8, 6, 11, 12], "Time step": [1] * 5,
        "class": [1, 3, 2, 3, 2]
    })
    edges = pd.DataFrame({"txId1": [10] * 4, "txId2": [12, 8, 11, 6]})
    snapshot = mod.neighborhood(10, nodes, edges, limit=2)
    assert snapshot["visibleNeighbors"] == 2
    assert snapshot["totalNeighbors"] == 4
    assert set(n["id"] for n in snapshot["nodes"]) == {"10", "6", "8"}


def test_pick_ids_is_deterministic_and_includes_unknowns():
    mod = exporter()
    records = pd.DataFrame({
        "txId": [1, 2, 3, 4], "Time step": [40] * 4,
        "class": [1, 2, 3, 3],
        "named_xgboost_graph": [.9, .8, .7, .6],
        "named_xgboost_tx": [.3, .4, .5, .6],
    })
    named = pd.DataFrame({"txId": [1]})
    ids = mod.pick_ids(records, named, per_step=1)
    assert ids == [1, 2, 3, 4]


def test_pack_record_preserves_unknown_label():
    mod = exporter()
    scores = pd.Series({
        "txId": 10, "Time step": 1, "class": 3,
        "named_xgboost_graph": .3, "named_xgboost_tx": .2,
    })
    frame = pd.DataFrame([{
        "txId": 10, "Time step": 1, "class": 3,
        **{f: np.nan for f in mod.FEATURES}
    }])
    edges = pd.DataFrame(columns=["txId1", "txId2"])
    shap = pd.DataFrame(columns=["txId", *mod.FEATURES])
    data = mod.pack_record(scores, frame, edges, shap, {})
    assert data["retrospectiveClass"] == 3
    assert data["network"]["visibleNeighbors"] == 0
    assert all(v is None for v in data["features"].values())
    assert data["shapLogOdds"] == {}
