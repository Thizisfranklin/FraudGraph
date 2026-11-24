"""Train a reproducible *research* XGBoost scoring bundle.

Chosen on historical validation only: expanding-history XGBoost, depth 3,
150 trees, learning rate 0.05 under the ASSUMPTION of a 2-bucket label lag.
This file contains an experimental, uncalibrated model, not a fraud verdict.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fraudgraph.adaptation import Specification, eligible_training, xgboost_pipeline
from fraudgraph.data import LOCAL
from fraudgraph.graph import GRAPH_FEATURES

ROOT = Path(__file__).resolve().parents[1]


def train_candidate(frame: pd.DataFrame, prediction_step=50, label_lag=2,
                    seed=42, threads=2):
    """Fit using only outcome labels assumed mature by the *future* scoring step.

    This is an as-of research scoring bundle: it has NOT been prospectively
    validated on unseen step 50 and no step-50 dataset is provided.
    """
    needed = {"Time step", "txId", "y", *LOCAL, *GRAPH_FEATURES}
    if not needed.issubset(frame):
        raise ValueError("Missing engineered attributes: " + str(sorted(needed-set(frame))))
    if prediction_step <= 49:
        raise ValueError("Research bundle reserved for hypothetical future step 50+")
    if frame.txId.duplicated().any():
        raise ValueError("Duplicated transaction identifiers")
    train, weights, cutoff = eligible_training(
        frame, prediction_step, "expanding", label_lag=label_lag
    )
    cols = list(LOCAL) + list(GRAPH_FEATURES)
    spec = Specification("expanding", max_depth=3, n_estimators=150,
                         learning_rate=.05)
    model = xgboost_pipeline(spec, seed=seed, threads=threads)
    model.fit(train[cols], train.y.astype(int),
              xgbclassifier__sample_weight=weights)
    if not np.all(np.isfinite(model.predict_proba(train[cols])[:, 1])):
        raise ValueError("Nonfinite training scores")
    stats = {
        "model_id": "fraudgraph-experimental-expanding-xgb-v1",
        "model_kind": "XGBoost with median imputation and named transaction plus graph context",
        "selection_basis": "Steps 35, 37 and 39; selected by worst validation AP under 2-step lag scenario",
        "validation_mean_ap": .814007,
        "validation_worst_ap": .750270,
        "selected_max_depth": spec.max_depth,
        "selected_trees": spec.n_estimators,
        "selected_learning_rate": spec.learning_rate,
        "prediction_step_assumed": int(prediction_step),
        "label_lag_assumed_buckets": int(label_lag),
        "max_labeled_training_step": int(cutoff),
        "fit_known_labeled_rows": int(len(train)),
        "training_illicit": int((train.y == 1).sum()),
        "training_licit": int((train.y == 0).sum()),
        "feature_columns": cols,
        "prediction_contract": "End-of-time-bucket batch scoring, only after valid as-of graph features exist",
        "calibrated_probability": False,
        "prospective_tested": False,
        "claim": "Investigation priority only; does not establish fraud, guilt, or wallet identity",
        "known_limitations": [
            "True label availability times are unknown: lag is a research assumption",
            "No future period beyond step 49 exists here for prospective evaluation",
            "Model may deteriorate under future feature or conditional-label shifts",
            "Unknown outcomes are excluded from supervised fit, not assigned licit labels",
            "Features use bucket-close graph context, not immediate live chain decisions",
        ],
    }
    return {"pipeline": model, "features": cols, "metadata": stats}


def build(root: Path, out: Path, prediction_step=50):
    input_path = root / "data/processed/transactions.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path}: run original pipeline first")
    frame = pd.read_parquet(input_path)
    bundle = train_candidate(frame, prediction_step=prediction_step)
    out.mkdir(parents=True, exist_ok=True)
    artifact = out / "experimental_model.joblib"
    joblib.dump(bundle, artifact, compress=3)
    metadata = bundle["metadata"]
    metadata["model_bundle_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (out / "model_card.json").write_text(json.dumps(metadata, indent=2),
                                         encoding="utf-8")
    print(f"Saved experimental XGBoost pipeline: {artifact}")
    print(f"Training labels through step {metadata['max_labeled_training_step']}, "
          f"to score hypothetical future step {prediction_step}.")
    print("No claim of prospective or production effectiveness.")
    return artifact


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, default=ROOT/"models/research_candidate")
    p.add_argument("--prediction-step", type=int, default=50)
    args = p.parse_args()
    build(args.root.resolve(), args.out.resolve(), args.prediction_step)


if __name__ == "__main__":
    main()
