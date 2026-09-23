# VERIFIED_PORTFOLIO_CLAIMS

Evidence run: `20260923T163139886696Z`. These are project outcomes, not a representation that the owner has independently mastered every implementation detail.

| Defensible claim | Direct evidence |
|---|---|
| Validated the full Elliptic++ transaction subset: 203,769 nodes, 234,355 edges, 49 steps | `reports/data_validation.json`, exact source hashes |
| Executed eight paired model/feature experiments using temporal splits | `reports/results.csv`, `reports/experiment_log.jsonl` |
| Added graph context to named transaction XGBoost, increasing test AP from 0.4239 to 0.5240 | `reports/results.csv`; AP delta +0.1000, time-bucket bootstrap interval [0.0015, 0.1365] |
| Found only +0.0049 AP incremental graph benefit with the stronger local-feature baseline | `reports/paired_comparison.json`; interval includes zero |
| Found graph-enhanced logistic models performed worse on pooled test AP | `reports/results.csv` |
| Captured 273 of 636 known illicit test transactions at 5% per-step all-traffic review capacity | `reports/review_capacity.csv`; 2337 reviews, 140 known licit, 1924 unknown |
| Detected severe late-period failure rather than claiming stable deployment performance | `reports/robustness.csv`, `reports/test_by_time.csv` |
| Executed label/future-invariance tests, SQL/graph parity, TreeSHAP additivity, and seven notebooks | `reports/tests.txt`, `reports/run_manifest.json`, executed notebook cells |

Do not claim a production deployment, real-time leakage-free authorization, 90% future precision, financial losses prevented, a GNN, PostgreSQL execution, customer-level fairness, or a universal benefit from graph features.


