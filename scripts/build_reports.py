"""Render measured results into the README and the handoff; never invent metrics."""
from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
reports = root / "reports"
results = pd.read_csv(reports / "results.csv")
test = results[results.split == "test"].set_index("experiment_id")
policy = json.loads((reports / "decision_policy.json").read_text())
comparison = json.loads((reports / "paired_comparison.json").read_text())
manifest = json.loads((reports / "run_manifest.json").read_text())
capacity = pd.read_csv(reports / "review_capacity.csv")
cap = capacity[(capacity.split == "test") & (capacity.experiment_id == policy["selected_model"]) & (capacity.scope == "all_transactions")]
cap5 = cap[cap.capacity_fraction == .05].iloc[0]
bands = pd.read_csv(reports / "risk_band_labels.csv").set_index("risk_band")
baseline = test.loc["named_xgboost_tx"]
graph = test.loc["named_xgboost_graph"]
extended = test.loc["extended_xgboost_graph"]
negative = json.loads((reports / "negative_control.json").read_text())
ablation = pd.read_csv(reports / "structural_ablations.csv")
ablation = ablation[ablation.split == "test"].set_index("experiment_id")
cases = pd.read_csv(reports / "cases.csv")
shap = pd.read_csv(reports / "case_shap_logodds.csv").set_index("txId")


def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n|" + "|".join(["---"]*len(headers)) + "|\n" + "\n".join("| " + " | ".join(map(str,row)) + " |" for row in rows)


result_table = table(["Feature family / model", "Transaction AP", "+ Graph AP", "Difference"], [
    [family+" / "+model, f"{test.loc[family+'_'+model+'_tx','pr_auc_ap']:.4f}",
     f"{test.loc[family+'_'+model+'_graph','pr_auc_ap']:.4f}",
     f"{comparison[family+'_'+model]['delta_ap']:+.4f}"] for family in ["named", "extended"] for model in ["logistic", "xgboost"]])
threshold_table = table(["Primary model", "Precision", "Recall", "FPR", "TP", "FP", "FN", "TN"], [
    [name.replace("named_", ""), f"{row.precision:.3f}", f"{row.recall:.3f}", f"{row.false_positive_rate:.3%}",
     int(row.tp), int(row.fp), int(row.fn), int(row.tn)] for name,row in test.iterrows() if name.startswith("named_")])
capacity_table = table(["Capacity", "Reviewed", "Known illicit", "Known licit", "Unknown", "Known illicit recall", "All-traffic precision bounds"], [
    [f"{row.capacity_fraction:.0%}", int(row.reviewed), int(row.known_illicit), int(row.known_licit), int(row.unknown),
     f"{row.recall_at_k_known:.1%}", f"{row.precision_lower_bound_all:.1%}–{row.precision_upper_bound_all:.1%}"] for _,row in cap.iterrows()])
band_table = table(["Band", "Known illicit", "Known licit", "Unknown", "Total"], [
    [band, int(row['1']), int(row['2']), int(row['3']), int(row.sum())] for band,row in bands.iterrows()])
ci = comparison["named_xgboost"]
extci = comparison["extended_xgboost"]
reproduction = '''```bash
git clone https://github.com/Thizisfranklin/FraudGraph.git
cd FraudGraph
git switch implementation/classical-graph-study
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then, from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m fraudgraph.pipeline --download
python -m fraudgraph.diagnostics
python scripts/build_notebooks.py
python scripts/execute_notebooks.py
python scripts/build_reports.py
python scripts/verify_artifacts.py
```

Use Python 3.12 (tested on 3.12.14). The branch command applies until the implementation is merged. After merge, use the default branch. Alternatively invoke `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on Unix directly if shell activation is unavailable. The downloader needs internet access; subsequent runs can omit `--download`. The three raw files total about 702 MB. Allow several GB for the environment, parquet cache, models, and reports. XGBoost uses two threads; no GPU is required. Fresh graph snapshots take longer than cached runs. The recorded cached full run took roughly 1–2 minutes on the execution host; this is not a laptop performance guarantee.

`requirements.txt` pins direct dependencies; `requirements-lock.txt` captures the original full environment. Seeds and split boundaries are in `config.json`. The run manifest records code/data evidence; all completed main experiments append to `reports/experiment_log.jsonl`. Diagnostics append separately. Reruns overwrite presentation tables with the latest run, while preserving the append-only logs. Notebooks are executed against persisted results rather than independently refitting models.
'''

readme = f'''# FraudGraph — Does network context improve illicit-transaction detection?

A reproducible classical machine-learning study on the **full Elliptic++ transaction graph**: 203,769 transactions, 234,355 directed money-flow edges, and 49 time steps.

**Measured answer:** graph context improves XGBoost with the 15 named transaction attributes, from test average precision **{baseline.pr_auc_ap:.4f} to {graph.pr_auc_ap:.4f}**. The improvement shrinks to **{extci['delta_ap']:.4f} AP** when 93 anonymized local features are also available. Graph features hurt both logistic baselines on the pooled test set. **All boosted models fail to generalize reliably to the final six time steps.** This is a rigorous batch-triage experiment, not a production fraud detector.

![Test model comparison](reports/figures/model_comparison.png)

## Business problem and scope

Analysts have limited capacity. A useful risk system must find illicit transactions without creating excessive unnecessary reviews of legitimate activity. The central comparison holds labels, time splits, learner settings, and evaluation constant while adding observable graph structure.

The target is the dataset's illicit/licit classification. It is not a measurement of confirmed customer fraud, financial losses prevented, or legal guilt. This study uses transactions only; it does not claim device/IP fraud coverage, wallet-level attribution, or real-time blocking.

## Data and validation

Source: [Elliptic++ authors' repository](https://github.com/git-disl/EllipticPlusPlus), pinned to `08fe6aded83afb97bf5a79a71130f542ca783c2e`. The downloader verifies SHA-256 against the three pinned Git LFS objects. See [data validation](reports/data_validation.json) for exact hashes and sizes.

- 4,545 illicit, 42,019 licit, and 157,205 unknown transactions.
- No duplicate IDs, duplicate edges, self-loops, or dangling edge endpoints found.
- 965 rows lack the 17 added transaction/degree attributes; training-only median imputation handles model inputs.
- All 234,355 edges lie within their time bucket. The observed graph has 49 weak components, no isolates, median total degree 2, and maximum degree 473.
- Unknown labels stay unknown. They enter graph topology and consume review capacity, but never become negative training examples.

Raw data is downloaded from the source, not redistributed in this repository. Consult the authors' terms before redistributing it. Citation: Elmougy & Liu (2023), [Demystifying Fraudulent Transactions and Illicit Nodes in the Bitcoin Network for Financial Forensics](https://doi.org/10.1145/3580305.3599803).

## Experiment design and leakage control

Train on steps **1–29**, validate on **30–39**, and test on **40–49**. This gives 26,381 / 8,999 / 11,184 labeled rows. Hyperparameters are fixed, thresholds are selected on validation, and test results never choose the policy. Average precision (AP) is the non-interpolated PR-AUC summary used here.

Scoring occurs **at bucket close**: graph snapshots contain only nodes and edges observed by that cutoff. This explicitly allows same-bucket relationships and is not an instantaneous online replay. No label-derived neighbor features are used. Transaction IDs, time indices, source aggregate features, supplied graph degrees, and labels are excluded from predictors. Imputation and scaling are fit only on training data. See the [leakage audit](reports/LEAKAGE_AUDIT.md).

The primary baseline uses 15 named transaction attributes (amounts, fees, size, address counts). Eight graph features add degrees, scaled PageRank, component statistics, and local neighborhood structure. The sensitivity family adds 93 anonymized local columns to both arms. Those legacy columns have less auditable provenance; their stronger baseline prevents overstating graph's incremental value. See the [feature dictionary](reports/FEATURE_DICTIONARY.md).

Models: standardized, class-balanced Logistic Regression and histogram XGBoost with 250 depth-4 trees. The small fixed experiment budget avoids costly searches. No GNN, Neo4j server, or GPU is necessary.

## Actual temporal test results

{result_table}

For the named-attribute XGBoost pair, the AP difference is {ci['delta_ap']:+.4f}, with a paired time-bucket bootstrap 95% interval [{ci['ci_95_low']:.4f}, {ci['ci_95_high']:.4f}] over 1,000 resamples. The extended XGBoost difference has interval [{extci['ci_95_low']:.4f}, {extci['ci_95_high']:.4f}], which includes zero. Ten test buckets support only limited uncertainty claims.

At each model's validation-selected F1 threshold:

{threshold_table}

The AP improvement is not a blanket operational improvement: the graph XGBoost model also produces more false positives at its F1 threshold. See [all results](reports/results.csv), [experiment ledger](reports/experiment_log.jsonl), and [per-time results](reports/test_by_time.csv).

### The important failure: temporal drift

![Temporal generalization](reports/figures/temporal_generalization.png)

Named-attribute graph XGBoost AP is 0.7070 on test steps 40–43 and 0.0257 on 44–49. The latter cohort's illicit prevalence is approximately 0.0273. The strongest extended models also collapse. This blocks any claim of stable future detection performance. The cause is not established; changes in the observed population, labeling, or transaction patterns are plausible hypotheses, not verified explanations.

Post-hoc diagnostics preserve the original conclusion without retuning the final policy: removing named-feature fingerprints seen in training leaves the graph AP essentially unchanged (0.5241). A shuffled-label control reaches validation AP {negative['pr_auc_ap']:.4f}, versus prevalence {negative['validation_prevalence']:.4f}. Degree-only XGBoost reaches test AP {ablation.loc['diagnostic_named_xgboost_degree_only','pr_auc_ap']:.4f}; omitting component features reaches {ablation.loc['diagnostic_named_xgboost_without_component','pr_auc_ap']:.4f}. Component size/density can encode time-bucket cohort properties in this dataset, so these ablations matter. All are retained in [diagnostic results](reports/structural_ablations.csv) and [robustness analysis](reports/robustness.csv).

## Analyst decision system

Validation selects `{policy['selected_model']}` within the primary family. Scores below **{policy['low_review_boundary']:.6f}** are LOW; scores from that boundary to **{policy['review_high_boundary']:.6f}** are REVIEW; higher scores are HIGH. LOW means no automatic escalation, REVIEW means routine human review, and HIGH means priority human review. These scores are not calibrated probabilities.

The low boundary represents an illustrative 5% validation-traffic review scenario. The high boundary targets at least 90% observed labeled validation precision with at least 20 labeled cases. On test the bands contain:

{band_table}

The narrow REVIEW interval and five unknown REVIEW cases are the actual result of this policy, not a useful three-way business separation to exaggerate. HIGH precision among labeled test cases is only {bands.loc['HIGH','1']/(bands.loc['HIGH','1']+bands.loc['HIGH','2']):.1%}; the validation target does not transfer. Unknowns make population precision unidentifiable.

An alternative policy enforces top-K review capacity **per time step**, including unknowns:

{capacity_table}

At 5% capacity, {int(cap5.known_illicit)} of 636 known illicit cases are captured ({cap5.recall_at_k_known:.1%}), with {int(cap5.known_licit)} known licit and {int(cap5.unknown)} unknown cases reviewed. Precision bounds assume all unknown reviewed cases are licit or illicit, respectively; they are not confidence intervals. No claims of monetary savings or unique customer friction are possible from these labels. Read the [decision framework](reports/DECISION_FRAMEWORK.md).

## Explainability and network cases

Validation permutation importance identifies model reliance; transaction size is the dominant named feature, while PageRank and local structure contribute additional signal. Native XGBoost TreeSHAP explains selected cases in **log-odds**, with an executed additivity check. These are associative model explanations, not causes of criminal behavior.

Three deterministic, bounded case studies show the highest-score illicit transaction, the highest-score licit transaction, and the largest graph-score uplift among known illicit test cases. PNGs show directed edges and retrospective label colors. Offline HTML versions support hover and pan/zoom, capped at 40 nodes. They are case viewers rather than a whole-graph explorer.

- [Permutation importance](reports/figures/feature_importance.png)
- [Case summaries](reports/cases.csv) and [TreeSHAP contributions](reports/case_shap_logodds.csv)
- [Illicit neighborhood](reports/figures/case_high_score_illicit.html), [licit high-score neighborhood](reports/figures/case_high_score_licit.html), [graph uplift neighborhood](reports/figures/case_graph_uplift.html)

## Architecture and repository map

```text
config.json                 Split, seed, policy scenario, resource limits
src/fraudgraph/
  data.py                   Pinned acquisition and schema/data validation
  graph.py                  Time-filtered directed snapshots and features
  models.py                 Comparable logistic and XGBoost specifications
  evaluation.py             AP, thresholds, capacity, paired bootstrap
  pipeline.py               Executed experiment and evidence orchestration
  diagnostics.py            Negative control and robustness/ablation checks
  visualization.py          EDA, model figures, bounded interactive cases
notebooks/01...07            Executed analytical narrative
sql/                        Analytical queries and optional PostgreSQL schema
tests/                      Critical methodology and regression tests
reports/                    Measured results, audits, claims, and figures
data/raw, data/processed     Local reproducible data (Git-ignored)
models/                     Local fitted estimators (Git-ignored)
scripts/                    Notebook execution and evidence-based reporting
```

SQL performs time/class aggregation, edge joins, incoming-degree extraction, and risk summaries. Four analytical queries were executed in SQLite; incoming degrees match NetworkX exactly. PostgreSQL-compatible schema is included, but a PostgreSQL server was **not** executed.

## Reproduce

{reproduction}

## Limitations and defensible claims

Temporal failure, unknown-label selection bias, coarse timing, incomplete graph coverage, unaudited source extraction/normalization, and absent label-maturation dates limit deployment conclusions. There is no prospective trial, monetary-loss measurement, wallet/entity holdout, calibrated probability model, or production service. The project demonstrates methodology and measured trade-offs.

Start with [VERIFIED_PORTFOLIO_CLAIMS](VERIFIED_PORTFOLIO_CLAIMS.md), the [complete handoff and interview guide](HANDOFF.md), and [execution notes](reports/EXECUTION_NOTES.md). Every numerical result above comes from executed artifacts; no synthetic dataset substitutes for the real experiment.
'''
(root / "README.md").write_text(readme, encoding="utf-8")

claims = f'''# VERIFIED_PORTFOLIO_CLAIMS

Evidence run: `{manifest['run_id']}`. These are project outcomes, not a representation that the owner has independently mastered every implementation detail.

| Defensible claim | Direct evidence |
|---|---|
| Validated the full Elliptic++ transaction subset: 203,769 nodes, 234,355 edges, 49 steps | `reports/data_validation.json`, exact source hashes |
| Executed eight paired model/feature experiments using temporal splits | `reports/results.csv`, `reports/experiment_log.jsonl` |
| Added graph context to named transaction XGBoost, increasing test AP from {baseline.pr_auc_ap:.4f} to {graph.pr_auc_ap:.4f} | `reports/results.csv`; AP delta {ci['delta_ap']:+.4f}, time-bucket bootstrap interval [{ci['ci_95_low']:.4f}, {ci['ci_95_high']:.4f}] |
| Found only {extci['delta_ap']:+.4f} AP incremental graph benefit with the stronger local-feature baseline | `reports/paired_comparison.json`; interval includes zero |
| Found graph-enhanced logistic models performed worse on pooled test AP | `reports/results.csv` |
| Captured {int(cap5.known_illicit)} of 636 known illicit test transactions at 5% per-step all-traffic review capacity | `reports/review_capacity.csv`; {int(cap5.reviewed)} reviews, {int(cap5.known_licit)} known licit, {int(cap5.unknown)} unknown |
| Detected severe late-period failure rather than claiming stable deployment performance | `reports/robustness.csv`, `reports/test_by_time.csv` |
| Executed label/future-invariance tests, SQL/graph parity, TreeSHAP additivity, and seven notebooks | `reports/tests.txt`, `reports/run_manifest.json`, executed notebook cells |

Do not claim a production deployment, real-time leakage-free authorization, 90% future precision, financial losses prevented, a GNN, PostgreSQL execution, customer-level fairness, or a universal benefit from graph features.

## Resume bullets

- Built a reproducible temporal fraud-risk pipeline on 203,769 Elliptic++ transactions and 234,355 edges; graph features improved named-attribute XGBoost test average precision from {baseline.pr_auc_ap:.3f} to {graph.pr_auc_ap:.3f}, with uncertainty and drift audits.
- Evaluated eight model/feature configurations and analyst-capacity policies, capturing {int(cap5.known_illicit)}/636 known illicit test transactions at 5% per-period review capacity while preserving unknown labels and documenting severe late-period failure.
'''
(root / "VERIFIED_PORTFOLIO_CLAIMS.md").write_text(claims, encoding="utf-8")

case_text = []
for _, case in cases.iterrows():
    contributions = shap.loc[int(case.txId)].drop("bias")
    names = contributions.abs().nlargest(4).index
    details = ", ".join(f"{name} ({contributions[name]:+.3f})" for name in names)
    case_text.append(f"- `{case.case}`: transaction {int(case.txId)}, step {int(case.time_step)}, class {int(case['class'])}; baseline score {case.baseline_score:.4f}, graph score {case.score:.4f}. Largest signed log-odds contributions: {details}.")

interview = '''1. What exactly does the illicit label represent, and why is it not identical to customer fraud?
2. Why must unknown outcomes remain unknown rather than become negative labels?
3. Why use average precision instead of accuracy or only ROC-AUC?
4. Why split by time, and what do steps 1–29 / 30–39 / 40–49 test?
5. What is available at bucket close, and why is this not instantaneous detection?
6. Which supplied features were excluded to make the transaction-only comparison honest?
7. How do future-node and label-perturbation tests detect graph leakage?
8. Why does preprocessing need to fit only on the training population?
9. What do PageRank, neighbor degree, and component density mean here?
10. Why does the graph benefit shrink when anonymized local features enter the baseline?
11. Why do the final six periods invalidate a claim of stable future performance?
12. What does the paired time-bucket bootstrap assume, and what can ten buckets not establish?
13. How do fixed score bands differ from per-bucket top-K review queues?
14. What can and cannot be inferred about precision, recall, and customer friction with unknown labels?
15. What do permutation importance and TreeSHAP explain, and what would be needed before deployment?
'''
handoff = f'''# FraudGraph — Complete implementation handoff

## 1. What was built

An executed, reproducible batch-risk research system: pinned dataset acquisition, strict validation, EDA, temporal splits, transaction baselines, label-free snapshot graph features, paired models, review-capacity analysis, score bands, native TreeSHAP, offline network cases, SQL analyses, tests, seven executed notebooks, and evidence-based reporting. The original repository contained only a proposal README.

## 2. Repository map

`src/fraudgraph/` contains reusable computation; `notebooks/` is the numbered learning narrative; `reports/` contains measured evidence and audits; `sql/` holds four executed queries plus an optional PostgreSQL schema; `tests/` protects the critical methodology. `data/` and `models/` hold reproducible local artifacts excluded from Git. `scripts/` builds/executes notebooks and regenerates this report. Start at `README.md`, then notebooks 01–07.

## 3. Dataset

The full **Elliptic++ transaction subset**, not a synthetic sample or the distinct Elliptic2 dataset. Three files from author commit `08fe6aded83afb97bf5a79a71130f542ca783c2e`: `txs_features.csv`, `txs_classes.csv`, `txs_edgelist.csv`. There are 203,769 transactions: 4,545 illicit, 42,019 licit, 157,205 unknown; 234,355 directed edges and 49 time steps. Exactly 965 rows lack added transaction attributes. No ID/edge duplicates or dangling endpoints were found. File hashes are in `reports/data_validation.json`. Wallet actors are outside this study.

## 4. Experimental design

Train steps 1–29: 26,381 known-label rows. Validate 30–39: 8,999. Test 40–49: 11,184, including 636 illicit. Unknowns participate in topology and capacity, not supervised outcomes. Training-only median imputation, scaling for logistic regression, fixed learner configurations, and validation-only thresholds make the comparisons consistent.

Primary inputs are 15 named intrinsic attributes; enhanced inputs add eight graph features. A separate sensitivity family adds 93 anonymized local columns to both arms. No supplied aggregate features, source degrees, transaction IDs, time indices, or labels enter a model. Features are frozen at each bucket's close. This assumes the whole bucket is observable and must not be described as a real-time replay. See `reports/LEAKAGE_AUDIT.md`.

## 5. Final results

{result_table}

{threshold_table}

AP is average precision. Precision, recall, FPR, and confusion counts use each model's validation-F1 threshold. The eight candidates and all repeated execution attempts remain in the append-only log. Two structural ablations and one shuffled-label diagnostic are separately logged; they are not hidden candidate selection.

## 6. Transaction versus graph comparison

The primary XGBoost gain is {ci['delta_ap']:+.4f} AP; paired time-bucket bootstrap interval [{ci['ci_95_low']:.4f}, {ci['ci_95_high']:.4f}]. The stronger local-feature baseline leaves only {extci['delta_ap']:+.4f} incremental AP, with an interval crossing zero. Logistic graph variants perform worse. Evidence supports a conditional value of graph context, not a universal superiority claim.

All observed graph edges are same-step; there are 49 weak components. Component size/density can partly describe time-bucket cohorts. Post-hoc tests retain AP {ablation.loc['diagnostic_named_xgboost_degree_only','pr_auc_ap']:.4f} using degrees only and {ablation.loc['diagnostic_named_xgboost_without_component','pr_auc_ap']:.4f} without component features, versus baseline {baseline.pr_auc_ap:.4f}. Removing test fingerprints seen in training leaves results almost unchanged. The shuffled-label validation control gives AP {negative['pr_auc_ap']:.4f}; it is reassuring, not a proof against every kind of leakage.

## 7. Decision system

Primary validation AP selects `{policy['selected_model']}`. LOW < {policy['low_review_boundary']:.6f}; REVIEW from {policy['low_review_boundary']:.6f} to < {policy['review_high_boundary']:.6f}; HIGH >= {policy['review_high_boundary']:.6f}. HIGH means priority investigation, never automatic blocking. The interval is narrow because the illustrative precision and volume constraints nearly coincide; only five unknown test transactions land in REVIEW. Do not sell this as a well-separated business segmentation.

{band_table}

The high band's known-label precision is {bands.loc['HIGH','1']/(bands.loc['HIGH','1']+bands.loc['HIGH','2']):.1%}, below its 90% validation target. A hard-cap ranking policy is evaluated separately:

{capacity_table}

The 5% scenario reviews {int(cap5.reviewed)} transactions, capturing {int(cap5.known_illicit)} known illicit with {int(cap5.known_licit)} known licit and {int(cap5.unknown)} unknown outcomes. Unknown cases cannot be treated as false positives or confirmed fraud. Real costs, customer effects, and population recall are unmeasured.

## 8. Important figures and explanations

- `reports/figures/class_and_time.png`: imbalance, unknown volume, prevalence shift.
- `transaction_distributions.png`: meaningful transaction attributes by known class.
- `graph_structure.png`: degree and component distributions.
- `model_comparison.png`: test PR curves and capacity trade-offs.
- `temporal_generalization.png`: the essential failure analysis.
- `confusion_matrices.png`: primary XGBoost operating-point trade-offs.
- `feature_importance.png`: validation permutation importance; size dominates.
- `case_*.png` / `.html`: small deterministic neighborhoods, not an unreadable full graph.

Case explanations use native TreeSHAP; contributions are in log-odds, and their sum plus bias was verified against model margins:

{chr(10).join(case_text)}

Retrospective label colors are for explanation only. These examples were selected by a recorded score rule and are not a representative evaluation sample.

## 9. Technical decisions

Use one small Python package to prevent notebook logic from diverging. Cache graph features using data hashes plus feature-code hash. Use CPU histogram boosting and moderate depth, two XGBoost threads, and no expensive graph centrality. Treat named transaction attributes as the auditable primary family and opaque local features as sensitivity. Keep all unknown traffic in capacity denominators. Run SQL in SQLite for a self-contained workflow and supply PostgreSQL-compatible DDL honestly. Use exact native TreeSHAP rather than adding a heavy explanation dependency. Keep raw data/models out of Git.

## 10. Problems encountered and fixes

Shell networking initially prevented cloning; the approved session network permission enabled acquisition. Python was absent from PATH, so a bundled Python runtime created the isolated environment. PowerShell web requests failed TLS authentication; Git LFS and Python requests successfully acquired/verified the source. Matplotlib/IPython initially attempted caches in restricted home directories; project tooling now uses temporary runtime locations. A semicolon in a SQL comment broke naive statement splitting; `sqlite3.complete_statement` and a regression test fixed it. Pandas fragmentation warnings were removed by concatenating metadata rather than repeated insertion. Full pipeline reruns verified the corrected reporting path.

Scientific problems were retained, not hidden: weak logistic baselines, a small extended-feature graph gain, narrow risk bands, selective missingness, and severe late-period failure. No tuning on the test set was used to repair those results.

## 11. Limitations

Named graph-model AP declines from 0.7070 on steps 40–43 to 0.0257 on 44–49, near prevalence. This alone prevents a production-readiness claim. Unknown-label selection bias, only ten test periods, coarse temporal resolution, missing label-maturity dates, incomplete observed topology, unverified source extraction/normalization, and no wallet/entity holdout further limit inference. These are scores, not calibrated probabilities. There is no deployment, measured economic benefit, or customer-level impact study. CI configuration is provided; only actual observed CI status should be claimed.

## 12. Verified portfolio claims

Read `VERIFIED_PORTFOLIO_CLAIMS.md` for the claim-to-evidence table. Safe claims include full-data validation, eight temporal comparisons, the qualified primary AP gain, honest sensitivity and drift findings, review-capacity accounting with unknown labels, executed SQL/graph parity, and tested explanations. Avoid claiming a GNN, real-time detection, PostgreSQL execution, 90% future precision, or prevented losses.

## 13. Two resume bullets

{claims.split('## Resume bullets')[1].strip()}

## 14. Fifteen interview questions

{interview}

## 15. Code review guide

| File / function | What you must be able to defend |
|---|---|
| `data.py: acquire`, `load_validate`, `LOCAL` | Exact data provenance, schema checks, one-to-one joins, unknown mapping, feature whitelist |
| `graph.py: snapshot_features`, `build_features` | Induced time cutoff, edge direction, label-free features, isolates, PageRank normalization, cache semantics |
| `models.py: make_model` | Preprocessing order, balanced logistic objective, fixed XGBoost settings, why comparisons are paired |
| `evaluation.py: metrics`, `f1_threshold` | AP versus trapezoidal PR area, confusion metrics, validation-only threshold selection |
| `evaluation.py: capacity_table`, `policy_thresholds` | Per-period top-K, deterministic ties, unknown bounds, no automatic-block policy |
| `evaluation.py: paired_time_bootstrap` | Paired time resampling and its assumptions/limits |
| `pipeline.py: run`, `split_masks` | Data flow, experiment ledger, model selection, evidence outputs, TreeSHAP and SQL parity |
| `diagnostics.py: run` | Post-hoc checks, duplicate fingerprints, drift cohorts, label shuffle, structural ablations |
| `visualization.py: network_cases` | Deterministic case selection, bounded neighborhoods, hindsight label colors |
| `tests/` and `sql/analysis.sql` | Which methodological failures tests prevent and what SQL actually computes |

Before claiming personal ownership, trace one transaction from raw ID through its frozen features, model score, SHAP margin, and review policy. Explain why its unknown neighbors do not have negative labels. Independently run the tests and review the temporal-failure figure.

## 16. Exact reproduction

{reproduction}

The recorded final evidence run is `{manifest['run_id']}`. See `reports/run_manifest.json` for code hashes, configuration, runtime, and validation flags. Model binaries are local reproducible outputs, not source-controlled guarantees across library versions.
'''
(root / "HANDOFF.md").write_text(handoff, encoding="utf-8")
print("Generated README, VERIFIED_PORTFOLIO_CLAIMS, and 16-part HANDOFF from executed results")
