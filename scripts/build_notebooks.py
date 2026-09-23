"""Build the ordered analytical narrative; execution is a separate explicit step."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
setup = '''from pathlib import Path
import json
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown
ROOT = Path.cwd()
if not (ROOT / "config.json").exists():
    ROOT = ROOT.parent
REPORTS = ROOT / "reports"
assert (REPORTS / "run_manifest.json").exists(), "Run python -m fraudgraph.pipeline --download first"
manifest = json.loads((REPORTS / "run_manifest.json").read_text())
print("Evidence run:", manifest["run_id"])
def figure(name):
    display(Image(filename=str(REPORTS / "figures" / name)))
'''

notebooks = [
    ("01_data_understanding", "Data provenance and validation", [
        ("md", "The unit is a Bitcoin transaction. Illicit=1, licit=2, unknown=3. Unknown labels are missing outcomes, not negative examples. These notebooks inspect the full executed pipeline, whose logic lives in `src/fraudgraph`; they do not silently retrain models."),
        ("code", 'validation = json.loads((REPORTS / "data_validation.json").read_text())\ndisplay(pd.Series({k:v for k,v in validation.items() if k not in ["files", "timesteps", "missing_by_column"]}))\ndisplay(pd.DataFrame(validation["files"]).T)'),
        ("code", 'f = pd.read_parquet(ROOT / "data/processed/transactions.parquet")\nassert f.txId.is_unique\nassert f.loc[f["class"] == 3, "y"].isna().all()\ndisplay(pd.crosstab(f["split"], f["class"]))\ndisplay(pd.read_csv(REPORTS / "missingness_by_split_class.csv"))'),
        ("md", "The 965 rows missing added transaction attributes are retained. Imputation fits only on known training outcomes. The raw source's SHA-256 hashes identify the exact data; dataset files are excluded from Git.")]),
    ("02_eda", "Class imbalance, transactions, and temporal drift", [
        ("code", 'figure("class_and_time.png")\nfigure("transaction_distributions.png")'),
        ("code", 'f = pd.read_parquet(ROOT / "data/processed/transactions.parquet")\nknown = f[f.y.notna()]\nsummary = known.groupby("split").y.agg(["size", "sum", "mean"])\nsummary.columns = ["labeled", "illicit", "illicit_prevalence"]\ndisplay(summary)'),
        ("md", "Pooled metrics can conceal changes in illicit prevalence and behavior. Compare validation with test before describing a model as stable. Histogram transforms are visualization choices, not extra model preprocessing. Unknown outcomes dominate the population and prevent population-wide performance claims.")]),
    ("03_transaction_baseline", "Transaction-only baselines", [
        ("md", "The primary baseline uses 15 named intrinsic attributes. A sensitivity analysis adds 93 anonymized local features. Supplied neighborhood aggregates and graph degree columns are excluded from both baselines. Logistic Regression is standardized and class-balanced; XGBoost uses a fixed 250-tree specification."),
        ("code", 'from fraudgraph.data import LOCAL\ndisplay(pd.Series(LOCAL, name="Primary predictors"))\nr = pd.read_csv(REPORTS / "results.csv")\ndisplay(r[r.experiment_id.str.endswith("_tx")][["experiment_id","split","pr_auc_ap","precision","recall","false_positive_rate","threshold"]])'),
        ("code", 'display(pd.read_csv(REPORTS / "splits.csv"))\ndisplay(Markdown((REPORTS / "LEAKAGE_AUDIT.md").read_text()))'),
        ("md", "Average precision is the non-interpolated PR summary used throughout. Threshold metrics use the validation-F1 optimum frozen before test evaluation. Accuracy is intentionally not the model-selection objective.")]),
    ("04_graph_analysis", "Observed transaction topology", [
        ("code", 'display(pd.Series(json.loads((REPORTS / "graph_validation.json").read_text())))\nfigure("graph_structure.png")'),
        ("md", "All released transaction edges lie within a time bucket. Components therefore do not provide a continuous bridge from training periods to future periods. A directed observed edge is not a claim that the released graph contains every transaction on Bitcoin."),
        ("code", 'display(pd.read_csv(REPORTS / "cases.csv"))\nfigure("case_high_score_illicit.png")\nfigure("case_high_score_licit.png")'),
        ("md", "The case rule is reproducible: highest-score known illicit, highest-score known licit, and largest graph-model score uplift among known illicit test cases. Colors use retrospective outcomes only for explanation. Each view is capped at 40 nodes; HTML versions provide hover details and pan/zoom.")]),
    ("05_graph_features", "Prediction-time feature availability", [
        ("code", 'display(Markdown((REPORTS / "FEATURE_DICTIONARY.md").read_text()))\ndisplay(pd.read_csv(REPORTS / "graph_feature_summary.csv"))'),
        ("code", 'from fraudgraph.graph import snapshot_features\nnodes = pd.DataFrame({"txId":[1,2,3], "Time step":[1,1,2]})\nedges = pd.DataFrame({"txId1":[1,2], "txId2":[2,3]})\na, g = snapshot_features(nodes, edges, 1)\nb, _ = snapshot_features(nodes.iloc[:2], edges.iloc[:1], 1)\npd.testing.assert_frame_equal(a,b)\nassert 3 not in g\ndisplay(a)'),
        ("md", "This executable toy check confirms that an edge to a future node cannot change the earlier snapshot. Full tests also perturb labels. The same-step graph is allowed only under the declared bucket-close contract. Instantaneous fraud interception would need finer timestamps and a different replay.")]),
    ("06_model_comparison", "Does graph context add information?", [
        ("code", 'r = pd.read_csv(REPORTS / "results.csv")\ndisplay(r[r.split == "test"][["experiment_id","pr_auc_ap","precision","recall","false_positive_rate","tp","fp","fn","tn"]])\nfigure("model_comparison.png")\nfigure("all_experiments.png")'),
        ("code", 'display(pd.DataFrame(json.loads((REPORTS / "paired_comparison.json").read_text())).T)\ndisplay(pd.read_csv(REPORTS / "robustness.csv"))\ndisplay(pd.read_csv(REPORTS / "structural_ablations.csv"))\nfigure("temporal_generalization.png")\nfigure("confusion_matrices.png")\ndisplay(pd.Series(json.loads((REPORTS / "negative_control.json").read_text())).drop(["feature_set","parameters"]))'),
        ("code", 'figure("feature_importance.png")\nshap = pd.read_csv(REPORTS / "case_shap_logodds.csv").set_index("txId")\nfor tx, contributions in shap.iterrows():\n    print("Transaction", tx, "— top signed log-odds contributions")\n    names = contributions.drop("bias").abs().nlargest(5).index\n    display(contributions[names])'),
        ("md", "Graph context improves the named-attribute boosted model, but its incremental gain is much smaller with the stronger local-feature baseline. Logistic graph variants deteriorate on test. Permutation importance measures model reliance under correlated predictors; TreeSHAP contributions sum to a model margin, not a causal explanation or a verified criminal motive.")]),
    ("07_decision_analysis", "Review capacity, thresholds, and friction", [
        ("code", 'policy = json.loads((REPORTS / "decision_policy.json").read_text())\ndisplay(pd.Series(policy))\ndisplay(pd.read_csv(REPORTS / "risk_band_labels.csv"))'),
        ("code", 'capacity = pd.read_csv(REPORTS / "review_capacity.csv")\nchosen = capacity[(capacity.split == "test") & (capacity.experiment_id == policy["selected_model"])]\ndisplay(chosen)'),
        ("md", "The fixed risk bands and top-K capacity policies are different. A fixed score threshold can exceed or undershoot staffing capacity as traffic changes. Top-K caps workload but does not enforce a minimum confidence. Unknown cases consume analyst time, with unknown investigative yield."),
        ("code", 'display(pd.read_csv(REPORTS / "sql_4.csv"))\ndisplay(Markdown((REPORTS / "DECISION_FRAMEWORK.md").read_text()))'),
        ("md", "HIGH means priority human review, not automatic blocking. A narrow REVIEW interval is a measured outcome of this illustrative policy, not a reason to tune thresholds on test. The large validation-to-test performance decline means prospective validation is required before deployment.")])
]

for filename, title, cells in notebooks:
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.cells = [nbf.v4.new_markdown_cell("# " + title), nbf.v4.new_code_cell(setup)]
    nb.cells += [nbf.v4.new_markdown_cell(text) if kind == "md" else nbf.v4.new_code_cell(text) for kind, text in cells]
    (ROOT / "notebooks").mkdir(exist_ok=True)
    nbf.write(nb, ROOT / "notebooks" / (filename + ".ipynb"))
print("Built seven analytical notebooks")
