#!/usr/bin/env python3
"""Generate the ONLY numerical research-data module for Neon Ledger City.

Source-of-truth: tracked FraudGraph original reports, plus pinned completed
GitHub Actions experiment artifacts. No interpolated or invented outcomes.

This script intentionally fails when required evidence is missing. All source
values are retained at their exact CSV precision in generated data.ts.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[1]
REQUIRED_ORIGINAL = [
    "reports/data_validation.json", "reports/graph_validation.json",
    "reports/results.csv", "reports/splits.csv", "reports/test_by_time.csv",
    "reports/class_by_time.csv", "reports/review_capacity.csv",
    "reports/robustness.csv", "reports/paired_comparison.json",
    "reports/structural_ablations.csv", "reports/permutation_importance.csv",
    "reports/graph_feature_summary.csv", "reports/missingness_by_split_class.csv",
    "reports/decision_policy.json", "reports/run_manifest.json",
    "reports/artifact_verification.json", "reports/cases.csv",
    "reports/negative_control.json", "reports/duplicate_audit.json",
    "app/public/investigations.json",
]
REQUIRED_TEMPORAL = [
    "adaptive_posthoc_test_by_time.csv", "adaptive_validation_folds.csv",
    "adaptive_validation_leaderboard.csv", "feature_drift_by_time.csv",
    "graph_ablation_by_time.csv", "label_score_drift_by_time.csv",
    "selection_manifest.json",
]
REQUIRED_ROBUSTNESS = [
    "regularization_validation_folds.csv", "regularization_validation_leaderboard.csv",
    "regularization_selected_per_lag.csv", "capacity_validation.csv",
    "regularization_manifest.json", "adaptive_validation_folds.csv",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        values = list(csv.DictReader(stream))
    for row in values:
        for key, value in list(row.items()):
            if value is None or value == "":
                row[key] = None
            elif re.fullmatch(r"[+-]?\d+", value):
                row[key] = int(value)
            else:
                try:
                    row[key] = float(value)
                except ValueError:
                    row[key] = value
    return values


def file_data(path):
    if path.suffix == ".csv":
        return read_csv(path)
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8").replace(": NaN", ": null"))
    raise ValueError(path)


def assert_sources(repo, temporal, robustness):
    items = [repo / n for n in REQUIRED_ORIGINAL]
    items += [temporal / n for n in REQUIRED_TEMPORAL]
    items += [robustness / n for n in REQUIRED_ROBUSTNESS]
    absent = [str(p) for p in items if not p.exists()]
    if absent:
        raise FileNotFoundError("Missing required research evidence:\n" + "\n".join(absent))


def short_metric(value, source, scope, unit="Average Precision"):
    return {
        "status": "verified", "value": value, "source": source,
        "scope": scope, "unit": unit,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--robustness", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=REPO / "story/src/data/data.ts")
    args = parser.parse_args()
    repo, temporal, robustness = (args.repo.resolve(), args.temporal.resolve(),
                                  args.robustness.resolve())
    assert_sources(repo, temporal, robustness)
    original = {Path(p).stem: file_data(repo / p) for p in REQUIRED_ORIGINAL}
    temp = {Path(p).stem: file_data(temporal / p) for p in REQUIRED_TEMPORAL}
    robust = {Path(p).stem: file_data(robustness / p) for p in REQUIRED_ROBUSTNESS}

    originals = original["results"]
    def ap(exp, split="test"):
        matches = [r for r in originals if r["experiment_id"] == exp and r["split"] == split]
        if len(matches) != 1:
            raise ValueError(f"Nonunique model result: {exp}, {split}")
        return matches[0]["pr_auc_ap"]
    exp = ["named_xgboost_tx", "named_xgboost_graph",
           "extended_xgboost_tx", "extended_xgboost_graph"]
    cap = [r for r in original["review_capacity"]
           if r["scope"] == "all_transactions" and r["split"] == "test"
           and r["experiment_id"] == "named_xgboost_graph"
           and r["capacity_fraction"] == 0.05]
    if len(cap) != 1:
        raise ValueError("Original 5% test-traffic queue missing")
    xgb = [ap(x) for x in exp]
    old_cases = original["cases"]
    uplift = next(x for x in old_cases if x["case"] == "graph_uplift")
    cohort = [r for r in original["robustness"]
              if r["experiment_id"] == "named_xgboost_graph"]
    # Distinct sources and scopes — never conflate an original saved run with a
    # reproduced case or with a retrospective, adaptive replay.
    metrics = {
        "namedXgbTxTest": short_metric(xgb[0], "reports/results.csv", "original chronological test"),
        "namedXgbGraphTest": short_metric(xgb[1], "reports/results.csv", "original chronological test"),
        "extendedXgbTxTest": short_metric(xgb[2], "reports/results.csv", "original chronological test"),
        "extendedXgbGraphTest": short_metric(xgb[3], "reports/results.csv", "original chronological test"),
        "originalReviewKnownIllicit": short_metric(cap[0]["known_illicit"], "reports/review_capacity.csv", "5% all-traffic original test", "cases"),
        "originalReviewKnownTotal": short_metric(next(x for x in original["splits"] if x["split"]=="test" and x["class"]==1)["count"], "reports/splits.csv", "original test known illicit", "cases"),
        "illustrativeOnly": short_metric(uplift["baseline_score"], "reports/cases.csv", "original saved case", "score"),
        "illustrativeWithGraph": short_metric(uplift["score"], "reports/cases.csv", "original saved case", "score"),
        "conceptDriftVerified": {"status": "awaiting", "value": None, "display": "-- awaiting data --",
                                 "reason": "No causal verification of changed P(Y|X)"},
        "freshFutureValidation": {"status": "awaiting", "value": None, "display": "-- awaiting data --",
                                  "reason": "No genuinely unseen future labeled period"},
        "actualLabelMaturation": {"status": "awaiting", "value": None, "display": "-- awaiting data --",
                                  "reason": "No actual label availability timestamps"},
        "moneyRecovered": {"status": "awaiting", "value": None, "display": "-- awaiting data --",
                           "reason": "No measured financial loss or recovered funds"},
    }
    class_totals = original["data_validation"]["class_counts"]
    if sum(class_totals.values()) != original["data_validation"]["nodes"]:
        raise ValueError("Class counts do not sum to transaction count")
    by_time = [r for r in original["test_by_time"] if r["experiment_id"] == "named_xgboost_graph"]
    if len(by_time) != 10:
        raise ValueError("Expected 10 original test time buckets")
    if len(robust["regularization_validation_folds"]) != 144:
        raise ValueError("Unexpected regularization fold count; investigate artifact")
    if len(robust["capacity_validation"]) != 27:
        raise ValueError("Unexpected validation review-capacity table")
    cases = original["investigations"]["transactions"]
    if len(cases) != 101 or len({r["id"] for r in cases}) != len(cases):
        raise ValueError("Case archive missing or contains duplicate IDs")
    chapters = [
        {"id":0,"act":1,"name":"The Entrance","subtitle":"One ordinary row. An extraordinary question.","interaction":"enter"},
        {"id":1,"act":1,"name":"One Transaction","subtitle":"A row can only tell part of the story.","interaction":"inspect"},
        {"id":2,"act":1,"name":"The Network","subtitle":"Follow the edges, keep the unknowns.","interaction":"network"},
        {"id":3,"act":1,"name":"The Uplift","subtitle":"The same case. A different context.","interaction":"toggle"},
        {"id":4,"act":1,"name":"It Depends","subtitle":"Not every model benefits.","interaction":"features"},
        {"id":5,"act":1,"name":"The Queue","subtitle":"Staff time isn't infinite.","interaction":"queue"},
        {"id":6,"act":1,"name":"The Plot Twist","subtitle":"The model fumbled. The evidence matters.","interaction":"timeline"},
        {"id":7,"act":2,"name":"Why Did It Break?","subtitle":"Several signals shifted. The cause is unresolved.","interaction":"drift"},
        {"id":8,"act":2,"name":"The Retraining Loop","subtitle":"Try a strategy. See only measured outcomes.","interaction":"retrain"},
        {"id":9,"act":2,"name":"Stress Tests","subtitle":"Simpler isn't always safer.","interaction":"stress"},
        {"id":10,"act":2,"name":"Analyst Budgets","subtitle":"Unknown cases still fill the queue.","interaction":"budgets"},
        {"id":11,"act":2,"name":"The Workbench","subtitle":"What the prototype can actually do.","interaction":"case"},
        {"id":12,"act":2,"name":"The Takeaway","subtitle":"A better question is its own result.","interaction":"share"},
    ]
    evidence = {
        "repository": "https://github.com/Thizisfranklin/FraudGraph",
        "originalRun": original["run_manifest"]["run_id"],
        "dataset": original["data_validation"],
        "graph": original["graph_validation"],
        "graphSummary": original["graph_feature_summary"],
        "splitCounts": original["splits"],
        "classByTime": original["class_by_time"],
        "originalResults": originals,
        "originalRobustness": original["robustness"],
        "timeAP": original["test_by_time"],
        "primaryTimeline": by_time,
        "originalReviewCapacity": original["review_capacity"],
        "decisionPolicy": original["decision_policy"],
        "duplicateAudit": original["duplicate_audit"],
        "permutationImportance": original["permutation_importance"],
        "missingness": original["missingness_by_split_class"],
        "pairedComparisons": original["paired_comparison"],
        "structuralAblations": original["structural_ablations"],
        "negativeControl": original["negative_control"],
        "verification": original["artifact_verification"],
        "runManifest": original["run_manifest"],
        "originalCases": old_cases,
        "investigator": cases,
        "temporal": {
            "validationFolds": temp["adaptive_validation_folds"],
            "leaderboard": temp["adaptive_validation_leaderboard"],
            "posthocReplay": temp["adaptive_posthoc_test_by_time"],
            "drift": temp["feature_drift_by_time"],
            "labelScore": temp["label_score_drift_by_time"],
            "graphAblation": temp["graph_ablation_by_time"],
            "manifest": temp["selection_manifest"],
        },
        "robustness": {
            "validationFolds": robust["regularization_validation_folds"],
            "leaderboard": robust["regularization_validation_leaderboard"],
            "selected": robust["regularization_selected_per_lag"],
            "capacity": robust["capacity_validation"],
            "manifest": robust["regularization_manifest"],
        },
        "metrics": metrics,
        "chapters": chapters,
        "notebooks": [
            {"name": "01_data_understanding.ipynb", "status": "executed"},
            {"name": "02_eda.ipynb", "status": "executed"},
            {"name": "03_transaction_baseline.ipynb", "status": "executed"},
            {"name": "04_graph_analysis.ipynb", "status": "executed"},
            {"name": "05_graph_features.ipynb", "status": "executed"},
            {"name": "06_model_comparison.ipynb", "status": "executed"},
            {"name": "07_decision_analysis.ipynb", "status": "executed"},
            {"name": "08_temporal_drift.ipynb", "status": "unexecuted exploration template"},
        ],
        "evidenceIndex": {
            "dataIntegrity": "reports/data_validation.json",
            "graphTopology": "reports/graph_validation.json",
            "sourceHashes": "reports/run_manifest.json",
            "decisionFramework": "reports/DECISION_FRAMEWORK.md",
            "leakageAudit": "reports/LEAKAGE_AUDIT.md",
            "sqlAudit": "reports/EXECUTION_NOTES.md",
            "featureDictionary": "reports/FEATURE_DICTIONARY.md",
            "temporalProtocol": "docs/TEMPORAL_DRIFT_STUDY.md",
            "regularizationProtocol": "docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md",
            "analystRoadmap": "docs/ANALYST_WORKBENCH_ROADMAP.md",
            "caseExamples": "reports/cases.csv",
            "reactInvestigator": "app/src/App.jsx",
            "modelBundleScript": "scripts/build_selected_research_model.py",
        },
        "policy": {
            "labelCaveat": "Illicit is the dataset's retrospective transaction label, never a claim of guilt.",
            "scoringCaveat": "Uncalibrated scores rank cases; they are not fraud probabilities.",
            "timeCaveat": "Batch end-of-time-bucket. Not instantaneous blockchain monitoring.",
            "populationCaveat": "Unknown outcomes are not licit; known-label recall is not true population recall.",
            "testCaveat": "Original test collapse informed later experiments; adaptive test replays are post-hoc.",
            "deploymentCaveat": "No verified operational effectiveness or prospective evaluation.",
        },
    }
    preamble = """/* GENERATED — do not edit manually.
 * Rebuild from tracked source reports + completed GitHub Actions experiments.
 * All research numbers in this story must originate here.
 */
export type EvidenceScope =
  | "original-report" | "temporal-validation" | "temporal-posthoc"
  | "robustness-validation" | "investigator-reproduction";
export type VerifiedMetric = {
  status:"verified"; value:number; source:string; scope:string; unit:string;
};
export type AwaitingMetric = {
  status:"awaiting"; value:null; display:"-- awaiting data --"; reason:string;
};
export type Metric = VerifiedMetric | AwaitingMetric;
export type TransactionCase = {
  id:string; timeStep:number; retrospectiveClass:number;
  caseType:string; scores:{graph:number;transaction:number};
  features:Record<string,number|null>;
  shapLogOdds:Record<string,number>;
  network:{nodes:Array<{id:string;label:string;retrospectiveClass:number;focus:boolean;timeStep:number}>;
    edges:Array<{source:string;target:string}>;
    totalNeighbors:number; visibleNeighbors:number};
};
"""
    module = preamble + "\nexport const data = " + json.dumps(evidence, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False) + " as const;\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(module, encoding="utf-8")
    print(f"Wrote {args.output}, {len(module)} bytes. No invented metrics.")
    print(f"Includes {len(originals)} original model rows, {len(by_time)} original test buckets, "
          f"{len(temp['adaptive_validation_folds'])} temporal validation folds, "
          f"{len(robust['regularization_validation_folds'])} regularization folds, "
          f"{len(cases)} authentic source-backed cases.")


if __name__ == "__main__":
    main()
