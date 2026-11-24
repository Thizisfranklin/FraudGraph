"""Score a trusted feature table with the experimental (uncalibrated) model bundle.

This does NOT look up live blockchain transactions. Input must be a CSV of
fully engineered, bucket-close transaction and graph features, produced by a
trusted source. Scores are ranked investigation priorities, NOT fraud verdicts.

IMPORTANT: joblib loading executes pickle code; never load untrusted bundles.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def score_batch(bundle, features: pd.DataFrame):
    """Infer from expected model features only; no labels or ID as predictors."""
    required = bundle["features"]
    missing = sorted(set(required)-set(features))
    if missing:
        raise ValueError("Missing engineered features: " + ", ".join(missing))
    if not features.index.is_unique:
        raise ValueError("Duplicate row index")
    input_features = features.loc[:,required].apply(pd.to_numeric, errors="raise")
    if np.isinf(input_features.to_numpy(dtype=float)).any():
        raise ValueError("Feature table contains infinite values")
    scores = bundle["pipeline"].predict_proba(input_features)[:, 1]
    if not np.isfinite(scores).all():
        raise ValueError("Nonfinite model scores")
    result = pd.DataFrame({"investigation_priority_score": scores}, index=features.index)
    if "txId" in features:
        if features.txId.duplicated().any():
            raise ValueError("Duplicate transaction IDs")
        result.insert(0, "txId", features["txId"])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True,
                   help="Trusted research model bundle from this project")
    p.add_argument("--features", type=Path, required=True,
                   help="Input CSV with all 23 engineered features")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    bundle = joblib.load(args.bundle)  # Trusted artifact only; joblib uses pickle.
    frame = pd.read_csv(args.features)
    out = score_batch(bundle, frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Saved {len(out)} investigation priority scores: {args.output}")
    print("WARNING: NOT calibrated fraud probabilities, live Bitcoin TXID lookup, or criminal verdicts.")


if __name__ == "__main__":
    main()
