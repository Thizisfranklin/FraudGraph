"""Generate exploratory drift, feature-ablation, and adaptation reports.

Requires the *original* project's raw-data pipeline to have produced
data/processed/transactions.parquet and per-split prediction files. The
new analyses are diagnostic; the already-inspected test data is NOT a
pristine holdout for revised hypotheses.
"""
from pathlib import Path
import argparse
import json
import sys

import pandas as pd

# Allow invocation from the repository root with no editable install.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fraudgraph.data import LOCAL
from fraudgraph.graph import GRAPH_FEATURES
from fraudgraph.drift import ranked_shift, score_and_label_summary
from fraudgraph.adaptation import (
    temporal_validation_search, evaluate_selected_on_future,
    feature_ablation_experiments,
)


def run(root: Path, include_posthoc_test: bool = False, label_lag: int = 2):
    inputs = [
        root / "data/processed/transactions.parquet",
        root / "data/processed/validation_predictions.parquet",
        root / "reports/predictions.parquet",
    ]
    missing = [p.relative_to(root) for p in inputs if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing generated inputs: " + ", ".join(map(str, missing)) +
            ". Run 'python -m fraudgraph.pipeline --download' first."
        )
    frame = pd.read_parquet(inputs[0])
    frame["Time step"] = frame["Time step"].astype(int)
    report_dir = root / "reports/exploratory"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Drift diagnosis: all earlier transactions (including unknown labels)
    # define a historical reference for unsupervised input comparisons.
    baseline = frame.loc[frame["Time step"] <= 29]
    cols = LOCAL + GRAPH_FEATURES
    drift = ranked_shift(frame, baseline, cols, range(30, 50))
    drift.to_csv(report_dir / "feature_drift_by_time.csv", index=False)

    # Saved original-model predictions only; do not silently retrain them.
    score_name = "named_xgboost_graph"
    parts = []
    for path in inputs[1:]:
        saved = pd.read_parquet(path)
        if score_name not in saved:
            raise KeyError(f"Missing {score_name} in {path}")
        parts.append(saved[["txId", score_name]])
    scores = pd.concat(parts, ignore_index=True)
    if scores.txId.duplicated().any():
        raise ValueError("Original scores must have unique transaction IDs")
    scored = frame.merge(scores, on="txId", how="left", validate="one_to_one")
    summary = score_and_label_summary(scored.loc[scored["Time step"] >= 30], score_name)
    summary.to_csv(report_dir / "label_score_drift_by_time.csv", index=False)

    # New ablations are additional post-hoc research, not replacements
    # for the project's preserved primary results.
    ablation = feature_ablation_experiments(frame, LOCAL, GRAPH_FEATURES)
    ablation.to_csv(report_dir / "graph_ablation_by_time.csv", index=False)

    # Select both training strategy and hyperparameters using only
    # earlier validation folds; do not select by later test scores.
    selected, val, leaderboard = temporal_validation_search(
        frame, LOCAL + GRAPH_FEATURES, label_lag=label_lag
    )
    val.to_csv(report_dir / "adaptive_validation_folds.csv", index=False)
    leaderboard.to_csv(report_dir / "adaptive_validation_leaderboard.csv", index=False)

    selection = {
        "selected_specification": selected.name,
        "strategy": selected.strategy, "hyperparameters": {
            "max_depth": selected.max_depth, "n_estimators": selected.n_estimators,
            "learning_rate": selected.learning_rate,
        },
        "validation_steps": [31, 33, 35, 37, 39],
        "assumed_label_lag_buckets": label_lag,
        "has_posthoc_test": bool(include_posthoc_test),
        "methodology": "Retrospective, hypothesis-generating. Test drift previously inspected.",
        "limitations": [
            "Label availability dates are unknown; label_lag is a scenario assumption.",
            "Unknown outcomes excluded from supervised model fitting and AP.",
            "No untouched future test period after these experiments.",
            "Per-step AP depends on known positive-class prevalence and small counts.",
        ],
    }
    if include_posthoc_test:
        future = evaluate_selected_on_future(
            frame, LOCAL + GRAPH_FEATURES, selected, label_lag=label_lag
        )
        future.to_csv(report_dir / "adaptive_posthoc_test_by_time.csv", index=False)
    (report_dir / "selection_manifest.json").write_text(
        json.dumps(selection, indent=2), encoding="utf-8"
    )
    print("Saved exploratory reports to", report_dir)
    print("Validation-selected:", selected.name)
    print("Test replay:", "POST-HOC INCLUDED" if include_posthoc_test else "not run")
    return selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--include-posthoc-test", action="store_true",
                        help="Run exploratory replay on previously inspected test periods")
    parser.add_argument("--label-lag", type=int, default=2,
                        help="Assumed time buckets until true labels can be used")
    args = parser.parse_args()
    run(args.root.resolve(), args.include_posthoc_test, args.label_lag)


if __name__ == "__main__":
    main()
