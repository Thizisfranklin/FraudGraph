"""Post-experiment robustness checks; never feed back into model selection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .data import LOCAL
from .graph import GRAPH_FEATURES
from .models import make_model
from .evaluation import metrics, f1_threshold, capacity_table


def run(root):
    f = pd.read_parquet(root / "data/processed/transactions.parquet")
    p = pd.read_parquet(root / "reports/predictions.parquet")
    config = json.loads((root / "config.json").read_text())
    hashes = pd.util.hash_pandas_object(f[LOCAL], index=False)
    train_hashes = set(hashes[f.split == "train"])
    feature_flags = pd.DataFrame({"txId": f.txId, "seen_train_fingerprint": hashes.isin(train_hashes),
                                 "missing_named": f[LOCAL].isna().any(axis=1)})
    p = p.merge(feature_flags, on="txId", validate="one_to_one")
    subsets = {"all_labeled_test": p.y.notna(),
               "exclude_train_fingerprints": p.y.notna() & ~p.seen_train_fingerprint,
               "complete_named_attributes": p.y.notna() & ~p.missing_named,
               "early_test_steps_40_43": p.y.notna() & (p["Time step"] <= 43),
               "late_test_steps_44_49": p.y.notna() & (p["Time step"] >= 44)}
    rows = []
    for subset, mask in subsets.items():
        q = p[mask]
        for column in p.columns:
            if column.startswith(("named_", "extended_")):
                rows.append({"cohort": subset, "experiment_id": column, "n": len(q), "illicit": int(q.y.sum()),
                             "ap": average_precision_score(q.y, q[column]) if q.y.sum() else None})
    pd.DataFrame(rows).to_csv(root / "reports/robustness.csv", index=False)
    missing = f.assign(missing_named=f[LOCAL].isna().any(axis=1)).groupby(["split", "class"]).agg(
        transactions=("txId", "size"), missing_named=("missing_named", "sum"))
    missing.to_csv(root / "reports/missingness_by_split_class.csv")
    f[GRAPH_FEATURES].agg(["min", "max", "mean", "std", "nunique"]).T.to_csv(root / "reports/graph_feature_summary.csv")
    # A diagnostic negative control chosen after the main experiment: not a contender.
    train = f[(f.split == "train") & f.y.notna()]
    val = f[(f.split == "validation") & f.y.notna()]
    cols = LOCAL + [c for c in f if c.startswith("Local_feature_")] + GRAPH_FEATURES
    shuffled = np.random.default_rng(config["seed"]).permutation(train.y.astype(int).to_numpy())
    model = make_model("xgboost", config["seed"], config["threads"])
    model.fit(train[cols], shuffled)
    result = {"experiment_id": "diagnostic_shuffled_labels_extended_xgboost_graph", "split": "validation",
              "feature_set": cols, "model": "xgboost", "parameters": model.steps[-1][1].get_params(),
              "pr_auc_ap": float(average_precision_score(val.y, model.predict_proba(val[cols])[:, 1])),
              "validation_prevalence": float(val.y.mean()), "seed": config["seed"],
              "notes": "Post-hoc negative control; train labels shuffled once. No test tuning or selection. Other operating metrics not applicable."}
    (root / "reports/negative_control.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Separate diagnostic log avoids mixing controls with production candidates.
    with (root / "reports/diagnostic_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ["feature_set", "parameters"]}, indent=2))
    # Component size is constant per time bucket here. Check whether the graph
    # result depends on those dataset-cohort signatures. Post-hoc, not selection.
    ablations = {
        "degree_only": ["g_in_degree", "g_out_degree", "g_total_degree"],
        "without_component": [c for c in GRAPH_FEATURES if not c.startswith("g_component_")],
    }
    rows = []
    test = f[(f.split == "test") & f.y.notna()]
    for name, graph_columns in ablations.items():
        columns = LOCAL + graph_columns
        model = make_model("xgboost", config["seed"], config["threads"])
        model.fit(train[columns], train.y.astype(int))
        threshold = f1_threshold(val.y, model.predict_proba(val[columns])[:, 1])
        for split, pool in [("validation", val), ("test", test)]:
            scores = model.predict_proba(pool[columns])[:, 1]
            cap = capacity_table(pool[["txId", "Time step", "y"]].assign(score=scores), "score", fractions=(.05,)).iloc[0]
            record = {"experiment_id": "diagnostic_named_xgboost_" + name, "split": split,
                      "threshold": threshold, **metrics(pool.y, scores, threshold),
                      "precision_at_5pct_known": float(cap.precision_at_k_known), "recall_at_5pct_known": float(cap.recall_at_k_known),
                      "feature_set": columns, "parameters": model.steps[-1][1].get_params(),
                      "notes": "Post-hoc structural ablation; same splits and learner; not used to retune or select final policy."}
            rows.append({k:v for k,v in record.items() if k not in ["feature_set", "parameters"]})
            with (root / "reports/diagnostic_log.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
    pd.DataFrame(rows).to_csv(root / "reports/structural_ablations.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    run(Path.cwd())
