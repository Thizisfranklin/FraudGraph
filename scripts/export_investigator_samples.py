"""Export reproducible real-case, bounded graph views for the React investigator.

Only existing Elliptic++ transaction IDs appear. This does not train or deploy a
new fraud model. Historical labels are included only as retrospective evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CASES = ("high_score_illicit", "high_score_licit", "graph_uplift")
FEATURES = ("size", "fees", "total_BTC", "num_input_addresses", "num_output_addresses",
            "g_in_degree", "g_out_degree", "g_neighbor_degree_mean", "g_pagerank_scaled",
            "g_component_size")


def pick_ids(pred: pd.DataFrame, saved_cases: pd.DataFrame, per_step=8):
    """Sample test cases by prespecified score ranks, not arbitrary made-up IDs."""
    needed = {"txId", "Time step", "class", "named_xgboost_graph", "named_xgboost_tx"}
    if not needed.issubset(pred):
        raise ValueError("Missing prediction columns: " + str(sorted(needed - set(pred))))
    picks = [int(x) for x in saved_cases.txId]
    for _, part in pred.groupby("Time step", sort=True):
        ranked = part.sort_values(["named_xgboost_graph", "txId"],
                                  ascending=[False, True])
        picks.extend(ranked.head(per_step).txId.astype(int))
        # Include contrasting cases without inventing labels.
        known_licit = ranked.loc[ranked["class"] == 2]
        picks.extend(known_licit.head(2).txId.astype(int))
        unknown = ranked.loc[ranked["class"] == 3]
        picks.extend(unknown.head(2).txId.astype(int))
    return list(dict.fromkeys(picks))


def neighborhood(center_id: int, nodes: pd.DataFrame, source_edges: pd.DataFrame,
                 limit=28):
    """Real, directed, time-visible one-hop edges around one central transaction."""
    frame = nodes.set_index("txId", drop=False)
    center_id = int(center_id)
    if center_id not in frame.index:
        raise ValueError(f"Missing graph center {center_id}")
    cutoff = int(frame.loc[center_id, "Time step"])
    visible = set(frame.index[frame["Time step"] <= cutoff].astype(int))
    candidates = source_edges.loc[
        ((source_edges.txId1 == center_id) | (source_edges.txId2 == center_id))
    ]
    candidates = candidates.loc[
        candidates.txId1.isin(visible) & candidates.txId2.isin(visible)
    ].drop_duplicates(subset=["txId1", "txId2"])
    candidates = candidates.sort_values(["txId1", "txId2"])
    neighbors = sorted(set(candidates.txId1).union(candidates.txId2) - {center_id})
    shown = set(neighbors[:limit])
    included = {center_id} | shown
    e = candidates.loc[candidates.txId1.isin(included) &
                       candidates.txId2.isin(included)]
    items = []
    for txid in [center_id, *sorted(shown)]:
        row = frame.loc[txid]
        items.append({
            "id": str(int(txid)),
            "label": "Focus" if txid == center_id else str(int(txid)),
            "timeStep": int(row["Time step"]),
            "retrospectiveClass": int(row["class"]),
            "focus": bool(txid == center_id),
        })
    edges = [{"source": str(int(row.txId1)), "target": str(int(row.txId2))}
             for row in e.itertuples(index=False)]
    return {"nodes": items, "edges": edges, "totalNeighbors": len(neighbors),
            "visibleNeighbors": len(shown)}


def pack_record(row: pd.Series, frame: pd.DataFrame, edges: pd.DataFrame,
                shap: pd.DataFrame, named_cases: dict):
    center = int(row.txId)
    source = frame.loc[frame.txId == center].iloc[0]
    features = {}
    for col in FEATURES:
        value = source[col]
        features[col] = float(value) if pd.notna(value) and np.isfinite(value) else None
    known = shap.loc[shap.txId == center]
    explanation = {}
    if len(known):
        for col in FEATURES:
            if col in known and pd.notna(known.iloc[0][col]):
                explanation[col] = float(known.iloc[0][col])
    return {
        "id": str(center),
        "timeStep": int(row["Time step"]),
        "retrospectiveClass": int(row["class"]),
        "model": "Original named-feature XGBoost comparison, frozen training",
        "scores": {
            "graph": float(row["named_xgboost_graph"]),
            "transaction": float(row["named_xgboost_tx"]),
        },
        "features": features,
        "shapLogOdds": explanation,
        "caseType": named_cases.get(center, "sampled_review_queue"),
        "network": neighborhood(center, frame[["txId", "Time step", "class"]],
                                edges),
    }


def export(root: Path, output: Path, per_step=8):
    frame = pd.read_parquet(root / "data/processed/transactions.parquet")
    pred = pd.read_parquet(root / "reports/predictions.parquet")
    edges = pd.read_csv(root / "data/raw/txs_edgelist.csv")
    cases = pd.read_csv(root / "reports/cases.csv")
    shap = pd.read_csv(root / "reports/case_shap_logodds.csv")
    if not frame.txId.is_unique or not pred.txId.is_unique:
        raise ValueError("Duplicated transaction IDs")
    pred = pred.set_index("txId").loc[pick_ids(pred, cases, per_step)].reset_index()
    named = dict(zip(cases.txId.astype(int), cases.case))
    results = [pack_record(row, frame, edges, shap, named)
               for _, row in pred.iterrows()]
    for case in cases.itertuples(index=False):
        example = next(x for x in results if x["id"] == str(int(case.txId)))
        # The independent saved case file must match predictions exactly.
        if not np.isclose(example["scores"]["graph"], case.score):
            raise ValueError(f"Historical graph score mismatch for {case.txId}")
        if not np.isclose(example["scores"]["transaction"], case.baseline_score):
            raise ValueError(f"Historical baseline mismatch for {case.txId}")
    payload = {
        "dataset": "Elliptic++ transaction network",
        "version": "saved original model, retrospective",
        "selection": "three published examples plus deterministic high-score, known-licit and unknown test-period samples",
        "warning": "Unknown labels are not negatives. No live Bitcoin identifier lookups, calibrated fraud probabilities, or automated decisions.",
        "transactions": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False),
                      encoding="utf-8")
    print(f"Exported {len(results)} genuine transaction cases to {output}")
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, default=ROOT / "app/public/investigations.json")
    args = p.parse_args()
    export(args.root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
