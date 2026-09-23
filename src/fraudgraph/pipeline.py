"""Run the entire scientific comparison and persist evidence."""
from pathlib import Path
import argparse
import datetime as dt
import json
import platform
import sqlite3
import subprocess
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score
from sklearn.inspection import permutation_importance
import xgboost as xgb
from .data import acquire, load_validate, LOCAL, digest
from .graph import build_features, GRAPH_FEATURES
from .models import make_model
from .evaluation import metrics, f1_threshold, policy_thresholds, capacity_table, paired_time_bootstrap
from . import visualization as viz


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=lambda x: x.item() if hasattr(x, "item") else str(x)), encoding="utf-8")


def split_masks(frame, config):
    t = frame["Time step"]
    return {"train": t <= config["train_end"],
            "validation": (t > config["train_end"]) & (t <= config["validation_end"]),
            "test": t > config["validation_end"]}


def sql_statements(text):
    """Preserve SQL comments and quoted semicolons when separating statements."""
    pending = ""
    for line in text.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            yield pending
            pending = ""
    if pending.strip() and any(not line.lstrip().startswith("--") for line in pending.splitlines() if line.strip()):
        raise ValueError("Incomplete SQL statement")


def run(root, download=False):
    start = time.time()
    config = json.loads((root / "config.json").read_text())
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for directory in ["data/raw", "data/processed", "reports/figures", "reports/runs", "models"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    if download: acquire(root)
    print("Loading and validating source CSVs", flush=True)
    frame, edges, validation = load_validate(root)
    dump(root / "reports/data_validation.json", validation)
    # Cache key incorporates raw data and the actual feature implementation.
    fingerprint = {"source": validation["files"], "implementation": digest(Path(__file__).with_name("graph.py"))}
    cache = root / "data/processed/graph_features.parquet"
    stamp = cache.with_suffix(".json")
    if cache.exists() and stamp.exists() and json.loads(stamp.read_text()) == fingerprint:
        import networkx as nx
        gf = pd.read_parquet(cache)
        graph = nx.from_pandas_edgelist(edges, "txId1", "txId2", create_using=nx.DiGraph)
        graph.add_nodes_from(frame.txId)
        print("Using verified graph-feature cache", flush=True)
    else:
        gf, graph, graph_stats = build_features(frame, edges)
        gf.to_parquet(cache, index=False)
        dump(stamp, fingerprint)
        dump(root / "reports/graph_validation.json", graph_stats)
    frame = frame.merge(gf, on="txId", validate="one_to_one")
    masks = split_masks(frame, config)
    frame = pd.concat([frame, pd.Series(np.select(list(masks.values()), list(masks), default="invalid"), index=frame.index, name="split")], axis=1)
    frame.to_parquet(root / "data/processed/transactions.parquet", index=False)
    split_summary = frame.groupby(["split", "class"]).size().rename("count").reset_index()
    split_summary.to_csv(root / "reports/splits.csv", index=False)
    hashes = pd.util.hash_pandas_object(frame[LOCAL], index=False)
    overlap = {}
    for left, right in [("train", "validation"), ("train", "test"), ("validation", "test")]:
        overlap[f"{left}_{right}_shared_local_fingerprints"] = len(set(hashes[masks[left]]) & set(hashes[masks[right]]))
        assert not set(frame.loc[masks[left], "txId"]) & set(frame.loc[masks[right], "txId"])
    dump(root / "reports/duplicate_audit.json", overlap)
    viz.eda(root, frame, graph, config)
    # Prespecified 2x2 primary comparison plus 2x2 local-feature sensitivity.
    extended = LOCAL + [c for c in frame if c.startswith("Local_feature_")]
    feature_sets = {"named": LOCAL, "extended": extended}
    ledger, capacities, fitted, feature_map = [], [], {}, {}
    test = frame.loc[masks["test"], ["txId", "Time step", "class", "y"]].copy()
    validation_scores = frame.loc[masks["validation"], ["txId", "Time step", "class", "y"]].copy()
    logpath = root / "reports/experiment_log.jsonl"
    for family, columns in feature_sets.items():
        for model_name in ["logistic", "xgboost"]:
            for context in ["tx", "graph"]:
                name = f"{family}_{model_name}_{context}"
                cols = columns + (GRAPH_FEATURES if context == "graph" else [])
                feature_map[name] = cols
                model = make_model(model_name, config["seed"], config["threads"])
                training = frame.loc[masks["train"] & frame.y.notna()]
                print(f"Training {name}: {len(training)} labeled rows, {len(cols)} features", flush=True)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ConvergenceWarning)
                    model.fit(training[cols], training.y.astype(int))
                model_warnings = [str(w.message) for w in caught]
                fitted[name] = model
                joblib.dump(model, root / "models" / f"{name}.joblib")
                va = frame.loc[masks["validation"]]
                va_score = model.predict_proba(va[cols])[:, 1]
                va_known = va.y.notna().to_numpy()
                threshold = f1_threshold(va.y[va_known], va_score[va_known])
                validation_scores[name] = va_score
                test[name] = model.predict_proba(frame.loc[masks["test"], cols])[:, 1]
                for split, pool, scores in [("validation", va, va_score), ("test", test, test[name].to_numpy())]:
                    known = pool.y.notna().to_numpy()
                    cap = capacity_table(pool[["txId", "Time step", "y"]].assign(score=scores), "score")
                    cap["experiment_id"], cap["split"] = name, split
                    capacities.append(cap)
                    k5 = cap[(cap.scope == "labeled_only") & (cap.capacity_fraction == .05)].iloc[0]
                    record = {"run_id": run_id, "experiment_id": name, "dataset": "Elliptic++ full transaction graph",
                              "split": split, "train_steps": f"1-{config['train_end']}",
                              "validation_steps": f"{config['train_end']+1}-{config['validation_end']}",
                              "test_steps": f"{config['validation_end']+1}-49", "feature_set": cols, "model": model_name,
                              "parameters": model.steps[-1][1].get_params(), "threshold": threshold,
                              **metrics(pool.y[known], scores[known], threshold),
                              "precision_at_5pct_known": float(k5.precision_at_k_known),
                              "recall_at_5pct_known": float(k5.recall_at_k_known),
                              "notes": "Fixed hyperparameters; threshold maximizes validation F1; no unknown labels in fitting.",
                              "warnings": model_warnings}
                    ledger.append(record)
                    with logpath.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(record, default=str) + "\n")
    results = pd.DataFrame([{k: v for k, v in row.items() if k not in ["parameters", "feature_set", "warnings"]} for row in ledger])
    results.to_csv(root / "reports/results.csv", index=False)
    caps = pd.concat(capacities, ignore_index=True)
    caps.to_csv(root / "reports/review_capacity.csv", index=False)
    test.to_parquet(root / "reports/predictions.parquet", index=False)
    validation_scores.to_parquet(root / "data/processed/validation_predictions.parquet", index=False)
    dump(root / "reports/feature_sets.json", feature_map)
    # Select operational model on primary validation AP only, irrespective of test.
    valid = results[(results.split == "validation") & results.experiment_id.str.startswith("named_")]
    chosen = valid.sort_values(["pr_auc_ap", "experiment_id"], ascending=[False, True]).iloc[0].experiment_id
    known = validation_scores.y.notna()
    low, high = policy_thresholds(validation_scores.loc[known, "y"], validation_scores.loc[known, chosen],
                                  validation_scores[chosen], config["review_fraction"], config["high_precision_target"], config["high_min_cases"])
    test["risk_band"] = np.where(test[chosen] >= high, "HIGH", np.where(test[chosen] >= low, "REVIEW", "LOW"))
    decision = {"selected_model": chosen, "low_review_boundary": low, "review_high_boundary": high if np.isfinite(high) else None,
                "high_enabled": bool(np.isfinite(high)), "high_precision_target": config["high_precision_target"],
                "review_fraction_validation": config["review_fraction"], "high_min_labeled_cases": config["high_min_cases"],
                "test_band_counts": test.risk_band.value_counts().to_dict(),
                "note": "High precision is empirical on labeled validation only; no guarantee on unknowns or future traffic. Null high boundary disables HIGH."}
    dump(root / "reports/decision_policy.json", decision)
    pd.crosstab(test.risk_band, test["class"]).to_csv(root / "reports/risk_band_labels.csv")
    per_time = []
    for name in fitted:
        for t, group in test[test.y.notna()].groupby("Time step"):
            per_time.append({"experiment_id": name, "time_step": t, "labeled": len(group), "illicit": int(group.y.sum()),
                             "ap": float(average_precision_score(group.y, group[name])) if group.y.sum() else None})
    pd.DataFrame(per_time).to_csv(root / "reports/test_by_time.csv", index=False)
    comparisons = {}
    for family in feature_sets:
        for model_name in ["logistic", "xgboost"]:
            prefix = f"{family}_{model_name}"
            comparisons[prefix] = paired_time_bootstrap(test, prefix+"_tx", prefix+"_graph", config["bootstrap_repetitions"], config["seed"])
    dump(root / "reports/paired_comparison.json", comparisons)
    print("Generating explanations and bounded network cases", flush=True)
    # Explain the graph model even when validation selects a transaction-only policy.
    explain_name = "named_xgboost_graph"
    model, cols = fitted[explain_name], feature_map[explain_name]
    va = frame.loc[masks["validation"] & frame.y.notna()]
    imp = permutation_importance(model, va[cols], va.y.astype(int), scoring="average_precision", n_repeats=3, random_state=config["seed"], n_jobs=1)
    importance = pd.DataFrame({"feature": cols, "mean_ap_drop": imp.importances_mean, "std_ap_drop": imp.importances_std}).sort_values("mean_ap_drop", ascending=False)
    importance.to_csv(root / "reports/permutation_importance.csv", index=False)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    top = importance.head(15).iloc[::-1]
    ax.barh(top.feature, top.mean_ap_drop, xerr=top.std_ap_drop)
    ax.set(xlabel="Validation AP decrease after permutation (3 repeats)", title="Graph-enhanced XGBoost: model reliance, not causation")
    viz.save(fig, root, "feature_importance.png")
    cases = viz.network_cases(root, frame, edges, test, explain_name, config["seed"])
    case_ids = [case["txId"] for case in cases]
    case_frame = frame.set_index("txId").loc[case_ids, cols]
    transformed = model.steps[0][1].transform(case_frame)
    booster = model.steps[-1][1].get_booster()
    contributions = booster.predict(xgb.DMatrix(transformed), pred_contribs=True)
    margin = booster.predict(xgb.DMatrix(transformed), output_margin=True)
    if not np.allclose(contributions.sum(axis=1), margin, atol=1e-4):
        raise ValueError("TreeSHAP additivity check failed")
    explanation = pd.DataFrame(contributions, columns=cols+["bias"])
    explanation.insert(0, "txId", case_ids)
    explanation.to_csv(root / "reports/case_shap_logodds.csv", index=False)
    viz.comparison(root, test, results, caps[caps.split == "test"])
    # Execute meaningful relational analyses locally; don't claim a PostgreSQL execution.
    with sqlite3.connect(root / "reports/analytics.sqlite") as conn:
        frame[["txId", "Time step", "class", "total_BTC", "fees"]].rename(columns={"txId":"tx_id", "Time step":"time_step", "total_BTC":"total_btc"}).to_sql("transactions", conn, if_exists="replace", index=False)
        edges.rename(columns={"txId1":"source", "txId2":"target"}).to_sql("edges", conn, if_exists="replace", index=False)
        test[["txId", "class", chosen, "risk_band"]].rename(columns={"txId":"tx_id", chosen:"score"}).to_sql("risk_scores", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS edges_target ON edges(target)")
        conn.execute("CREATE INDEX IF NOT EXISTS tx_id_idx ON transactions(tx_id)")
        for i, statement in enumerate(sql_statements((root / "sql/analysis.sql").read_text())):
            if "SELECT" in statement:
                out = pd.read_sql_query(statement, conn)
                out.to_csv(root / "reports" / f"sql_{i+1}.csv", index=False)
                if "visible_in_degree" in out:
                    merged = out.merge(gf, left_on="tx_id", right_on="txId", validate="one_to_one")
                    assert np.array_equal(merged.visible_in_degree, merged.g_in_degree)
    evidence = {"run_id": run_id, "config": config, "seconds": round(time.time()-start, 2),
                "python": platform.python_version(), "platform": platform.platform(), "experiments": len(fitted),
                "tree_shap_additivity_passed": True, "sql_graph_degree_parity_passed": True,
                "source_code_sha256": {p.name: digest(p) for p in Path(__file__).parent.glob("*.py")},
                "results_sha256": digest(root / "reports/results.csv")}
    dump(root / "reports/run_manifest.json", evidence)
    dump(root / "reports/runs" / f"{run_id}.json", {"manifest": evidence, "experiments": ledger})
    print(f"COMPLETE: {run_id}; {evidence['seconds']} seconds; selected policy {chosen}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    run(args.root.resolve(), args.download)


if __name__ == "__main__":
    main()
