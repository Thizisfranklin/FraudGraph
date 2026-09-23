# FraudGraph — Complete implementation handoff

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

| Feature family / model | Transaction AP | + Graph AP | Difference |
|---|---|---|---|
| named / logistic | 0.0906 | 0.0696 | -0.0210 |
| named / xgboost | 0.4239 | 0.5240 | +0.1000 |
| extended / logistic | 0.1496 | 0.1162 | -0.0333 |
| extended / xgboost | 0.6349 | 0.6398 | +0.0049 |

| Primary model | Precision | Recall | FPR | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| logistic_tx | 0.084 | 0.832 | 54.617% | 529 | 5761 | 107 | 4787 |
| logistic_graph | 0.076 | 0.642 | 47.118% | 408 | 4970 | 228 | 5578 |
| xgboost_tx | 0.728 | 0.429 | 0.967% | 273 | 102 | 363 | 10446 |
| xgboost_graph | 0.735 | 0.484 | 1.052% | 308 | 111 | 328 | 10437 |

AP is average precision. Precision, recall, FPR, and confusion counts use each model's validation-F1 threshold. The eight candidates and all repeated execution attempts remain in the append-only log. Two structural ablations and one shuffled-label diagnostic are separately logged; they are not hidden candidate selection.

## 6. Transaction versus graph comparison

The primary XGBoost gain is +0.1000 AP; paired time-bucket bootstrap interval [0.0015, 0.1365]. The stronger local-feature baseline leaves only +0.0049 incremental AP, with an interval crossing zero. Logistic graph variants perform worse. Evidence supports a conditional value of graph context, not a universal superiority claim.

All observed graph edges are same-step; there are 49 weak components. Component size/density can partly describe time-bucket cohorts. Post-hoc tests retain AP 0.4683 using degrees only and 0.5057 without component features, versus baseline 0.4239. Removing test fingerprints seen in training leaves results almost unchanged. The shuffled-label validation control gives AP 0.0978; it is reassuring, not a proof against every kind of leakage.

## 7. Decision system

Primary validation AP selects `named_xgboost_graph`. LOW < 0.807129; REVIEW from 0.807129 to < 0.808545; HIGH >= 0.808545. HIGH means priority investigation, never automatic blocking. The interval is narrow because the illustrative precision and volume constraints nearly coincide; only five unknown test transactions land in REVIEW. Do not sell this as a well-separated business segmentation.

| Band | Known illicit | Known licit | Unknown | Total |
|---|---|---|---|---|
| HIGH | 291 | 76 | 1312 | 1679 |
| LOW | 345 | 10472 | 34146 | 44963 |
| REVIEW | 0 | 0 | 5 | 5 |

The high band's known-label precision is 79.3%, below its 90% validation target. A hard-cap ranking policy is evaluated separately:

| Capacity | Reviewed | Known illicit | Known licit | Unknown | Known illicit recall | All-traffic precision bounds |
|---|---|---|---|---|---|---|
| 1% | 471 | 83 | 18 | 370 | 13.1% | 17.6%–96.2% |
| 2% | 938 | 142 | 52 | 744 | 22.3% | 15.1%–94.5% |
| 5% | 2337 | 273 | 140 | 1924 | 42.9% | 11.7%–94.0% |
| 10% | 4670 | 324 | 530 | 3816 | 50.9% | 6.9%–88.7% |
| 20% | 9333 | 389 | 1427 | 7517 | 61.2% | 4.2%–84.7% |

The 5% scenario reviews 2337 transactions, capturing 273 known illicit with 140 known licit and 1924 unknown outcomes. Unknown cases cannot be treated as false positives or confirmed fraud. Real costs, customer effects, and population recall are unmeasured.

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

- `high_score_illicit`: transaction 12662327, step 41, class 1; baseline score 0.8936, graph score 0.9839. Largest signed log-odds contributions: size (+3.297), fees (+1.024), num_output_addresses (+0.407), g_component_size (+0.325).
- `high_score_licit`: transaction 72687354, step 42, class 2; baseline score 0.9068, graph score 0.9559. Largest signed log-odds contributions: size (+3.648), fees (+0.584), num_output_addresses (+0.490), g_out_degree (+0.245).
- `graph_uplift`: transaction 12661223, step 41, class 1; baseline score 0.2992, graph score 0.6890. Largest signed log-odds contributions: size (+2.534), in_BTC_min (-1.086), fees (+0.773), g_component_size (+0.399).

Retrospective label colors are for explanation only. These examples were selected by a recorded score rule and are not a representative evaluation sample.

## 9. Technical decisions

Use one small Python package to prevent notebook logic from diverging. Cache graph features using data hashes plus feature-code hash. Use CPU histogram boosting and moderate depth, two XGBoost threads, and no expensive graph centrality. Treat named transaction attributes as the auditable primary family and opaque local features as sensitivity. Keep all unknown traffic in capacity denominators. Run SQL in SQLite for a self-contained workflow and supply PostgreSQL-compatible DDL honestly. Use exact native TreeSHAP rather than adding a heavy explanation dependency. Keep raw data/models out of Git.

## 10. Problems encountered and fixes

Shell networking initially prevented cloning; the approved session network permission enabled acquisition. Python was absent from PATH, so a bundled Python runtime created the isolated environment. PowerShell web requests failed TLS authentication; Git LFS and Python requests successfully acquired/verified the source. Matplotlib/IPython initially attempted caches in restricted home directories; project tooling now uses temporary runtime locations. A semicolon in a SQL comment broke naive statement splitting; `sqlite3.complete_statement` and a regression test fixed it. Pandas fragmentation warnings were removed by concatenating metadata rather than repeated insertion. Full pipeline reruns verified the corrected reporting path.

Scientific problems were retained, not hidden: weak logistic baselines, a small extended-feature graph gain, narrow risk bands, selective missingness, and severe late-period failure. No tuning on the test set was used to repair those results.

## 11. Limitations

Named graph-model AP declines from 0.7070 on steps 40–43 to 0.0257 on 44–49, near prevalence. This alone prevents a production-readiness claim. Unknown-label selection bias, only ten test periods, coarse temporal resolution, missing label-maturity dates, incomplete observed topology, unverified source extraction/normalization, and no wallet/entity holdout further limit inference. These are scores, not calibrated probabilities. There is no deployment, measured economic benefit, or customer-level impact study. CI configuration is provided; only actual observed CI status should be claimed.



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


The recorded final evidence run is `20260923T163139886696Z`. See `reports/run_manifest.json` for code hashes, configuration, runtime, and validation flags. Model binaries are local reproducible outputs, not source-controlled guarantees across library versions.
