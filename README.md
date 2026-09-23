# FraudGraph — Does network context improve illicit-transaction detection?

A reproducible classical machine-learning study on the **full Elliptic++ transaction graph**: 203,769 transactions, 234,355 directed money-flow edges, and 49 time steps.

**Measured answer:** graph context improves XGBoost with the 15 named transaction attributes, from test average precision **0.4239 to 0.5240**. The improvement shrinks to **0.0049 AP** when 93 anonymized local features are also available. Graph features hurt both logistic baselines on the pooled test set. **All boosted models fail to generalize reliably to the final six time steps.** This is a rigorous batch-triage experiment, not a production fraud detector.

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

| Feature family / model | Transaction AP | + Graph AP | Difference |
|---|---|---|---|
| named / logistic | 0.0906 | 0.0696 | -0.0210 |
| named / xgboost | 0.4239 | 0.5240 | +0.1000 |
| extended / logistic | 0.1496 | 0.1162 | -0.0333 |
| extended / xgboost | 0.6349 | 0.6398 | +0.0049 |

For the named-attribute XGBoost pair, the AP difference is +0.1000, with a paired time-bucket bootstrap 95% interval [0.0015, 0.1365] over 1,000 resamples. The extended XGBoost difference has interval [-0.0008, 0.0115], which includes zero. Ten test buckets support only limited uncertainty claims.

At each model's validation-selected F1 threshold:

| Primary model | Precision | Recall | FPR | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| logistic_tx | 0.084 | 0.832 | 54.617% | 529 | 5761 | 107 | 4787 |
| logistic_graph | 0.076 | 0.642 | 47.118% | 408 | 4970 | 228 | 5578 |
| xgboost_tx | 0.728 | 0.429 | 0.967% | 273 | 102 | 363 | 10446 |
| xgboost_graph | 0.735 | 0.484 | 1.052% | 308 | 111 | 328 | 10437 |

The AP improvement is not a blanket operational improvement: the graph XGBoost model also produces more false positives at its F1 threshold. See [all results](reports/results.csv), [experiment ledger](reports/experiment_log.jsonl), and [per-time results](reports/test_by_time.csv).

### The important failure: temporal drift

![Temporal generalization](reports/figures/temporal_generalization.png)

Named-attribute graph XGBoost AP is 0.7070 on test steps 40–43 and 0.0257 on 44–49. The latter cohort's illicit prevalence is approximately 0.0273. The strongest extended models also collapse. This blocks any claim of stable future detection performance. The cause is not established; changes in the observed population, labeling, or transaction patterns are plausible hypotheses, not verified explanations.

Post-hoc diagnostics preserve the original conclusion without retuning the final policy: removing named-feature fingerprints seen in training leaves the graph AP essentially unchanged (0.5241). A shuffled-label control reaches validation AP 0.0978, versus prevalence 0.1153. Degree-only XGBoost reaches test AP 0.4683; omitting component features reaches 0.5057. Component size/density can encode time-bucket cohort properties in this dataset, so these ablations matter. All are retained in [diagnostic results](reports/structural_ablations.csv) and [robustness analysis](reports/robustness.csv).

## Analyst decision system

Validation selects `named_xgboost_graph` within the primary family. Scores below **0.807129** are LOW; scores from that boundary to **0.808545** are REVIEW; higher scores are HIGH. LOW means no automatic escalation, REVIEW means routine human review, and HIGH means priority human review. These scores are not calibrated probabilities.

The low boundary represents an illustrative 5% validation-traffic review scenario. The high boundary targets at least 90% observed labeled validation precision with at least 20 labeled cases. On test the bands contain:

| Band | Known illicit | Known licit | Unknown | Total |
|---|---|---|---|---|
| HIGH | 291 | 76 | 1312 | 1679 |
| LOW | 345 | 10472 | 34146 | 44963 |
| REVIEW | 0 | 0 | 5 | 5 |

The narrow REVIEW interval and five unknown REVIEW cases are the actual result of this policy, not a useful three-way business separation to exaggerate. HIGH precision among labeled test cases is only 79.3%; the validation target does not transfer. Unknowns make population precision unidentifiable.

An alternative policy enforces top-K review capacity **per time step**, including unknowns:

| Capacity | Reviewed | Known illicit | Known licit | Unknown | Known illicit recall | All-traffic precision bounds |
|---|---|---|---|---|---|---|
| 1% | 471 | 83 | 18 | 370 | 13.1% | 17.6%–96.2% |
| 2% | 938 | 142 | 52 | 744 | 22.3% | 15.1%–94.5% |
| 5% | 2337 | 273 | 140 | 1924 | 42.9% | 11.7%–94.0% |
| 10% | 4670 | 324 | 530 | 3816 | 50.9% | 6.9%–88.7% |
| 20% | 9333 | 389 | 1427 | 7517 | 61.2% | 4.2%–84.7% |

At 5% capacity, 273 of 636 known illicit cases are captured (42.9%), with 140 known licit and 1924 unknown cases reviewed. Precision bounds assume all unknown reviewed cases are licit or illicit, respectively; they are not confidence intervals. No claims of monetary savings or unique customer friction are possible from these labels. Read the [decision framework](reports/DECISION_FRAMEWORK.md).

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

```bash
git clone https://github.com/Thizisfranklin/FraudGraph.git
cd FraudGraph
git switch implementation/classical-graph-study
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
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


## Limitations and defensible claims

Temporal failure, unknown-label selection bias, coarse timing, incomplete graph coverage, unaudited source extraction/normalization, and absent label-maturation dates limit deployment conclusions. There is no prospective trial, monetary-loss measurement, wallet/entity holdout, calibrated probability model, or production service. The project demonstrates methodology and measured trade-offs.

Start with [VERIFIED_PORTFOLIO_CLAIMS](VERIFIED_PORTFOLIO_CLAIMS.md), the [complete handoff and interview guide](HANDOFF.md), and [execution notes](reports/EXECUTION_NOTES.md). Every numerical result above comes from executed artifacts; no synthetic dataset substitutes for the real experiment.
