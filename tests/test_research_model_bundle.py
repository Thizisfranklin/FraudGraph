from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd
import pytest

from fraudgraph.data import LOCAL
from fraudgraph.graph import GRAPH_FEATURES


def module_for(name):
    path = Path(__file__).resolve().parents[1]/"scripts"/(name+".py")
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def toy_frame():
    rows = []
    for step in range(1, 50):
        for i in range(6):
            cols = {c: float((i+1)*(step%3+1)) for c in [*LOCAL,*GRAPH_FEATURES]}
            rows.append({"txId": 100*step+i, "Time step": step,
                         "y": np.nan if i==5 else float(i%2), **cols})
    return pd.DataFrame(rows)


def test_candidate_fits_only_available_labels_for_step50(toy_frame):
    trainer = module_for("build_selected_research_model")
    b = trainer.train_candidate(toy_frame, prediction_step=50, label_lag=2)
    assert b["metadata"]["max_labeled_training_step"] == 48
    assert b["metadata"]["prediction_step_assumed"] == 50
    assert b["metadata"]["fit_known_labeled_rows"] == 48*5
    assert not b["metadata"]["prospective_tested"]
    assert len(b["features"]) == len(LOCAL) + len(GRAPH_FEATURES)
    with pytest.raises(ValueError, match="future step"):
        trainer.train_candidate(toy_frame, prediction_step=49)


def test_research_scoring_never_uses_target_column(toy_frame):
    trainer = module_for("build_selected_research_model")
    scorer = module_for("score_research_batch")
    b = trainer.train_candidate(toy_frame, prediction_step=50, label_lag=2)
    inputs = toy_frame.loc[:3, ["txId", "y", *b["features"]]].copy()
    before = scorer.score_batch(b, inputs)
    inputs["y"] = 1-inputs["y"]
    after = scorer.score_batch(b, inputs)
    assert np.allclose(before.investigation_priority_score,
                       after.investigation_priority_score)
    assert before.txId.tolist() == inputs.txId.tolist()
    assert before.investigation_priority_score.between(0,1).all()


def test_research_scoring_rejects_missing_and_infinite(toy_frame):
    trainer = module_for("build_selected_research_model")
    scorer = module_for("score_research_batch")
    b = trainer.train_candidate(toy_frame, prediction_step=50, label_lag=2)
    inputs = toy_frame.head(3).copy()
    with pytest.raises(ValueError, match="Missing engineered"):
        scorer.score_batch(b, inputs.drop(columns=b["features"][0]))
    inputs.loc[inputs.index[0], b["features"][0]] = np.inf
    with pytest.raises(ValueError, match="infinite"):
        scorer.score_batch(b, inputs)
