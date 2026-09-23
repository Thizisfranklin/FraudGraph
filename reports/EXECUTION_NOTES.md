# Execution and review notes

## Environment and completion

The implementation was executed locally with Python 3.12.14 in an isolated environment. Direct dependencies are pinned; the full resolved environment is captured separately. The source data is real, full-size Elliptic++ transaction data. No synthetic observations enter the measured results; small synthetic fixtures are used only for unit tests.

All eight main candidate experiments ran. Repeated runs are retained in the append-only experiment log and identified by run ID, rather than being selected for favorable metrics. The first full attempt completed modeling/explanations but failed during SQL reporting. The corrected pipeline subsequently completed twice, including the final visualization/reporting pass. The latest complete run manifest identifies the final reported results.

The graph cache is fingerprinted by source hashes and graph implementation hash. Cache use does not skip raw data validation or model training. The final cached run took 72.01 seconds on this host; a cold run must additionally compute 49 graph snapshots. This timing excludes dependency installation and source download and should not be presented as a general hardware benchmark.

## Engineering failures fixed

- Restricted shell networking initially blocked Git. Session network permission was granted and the clone completed.
- Python was not on PATH. A bundled runtime was located and used to create an isolated virtual environment.
- PowerShell HTTP requests failed TLS authentication. Git LFS retrieved the authors' data, and Python requests subsequently verified all three pinned LFS hashes. The public downloader uses Python requests.
- A full upstream clone initially retrieved actor files as well. The reproducible downloader was narrowed to the three transaction files; actor data never enters this experiment.
- Pandas fragmentation warnings were removed by concatenating metadata columns instead of repeated insertion.
- Matplotlib and IPython initially attempted caches in restricted home directories. Temporary runtime/cache paths now keep execution self-contained.
- Naively splitting SQL on every semicolon also split a comment. The fix uses SQLite's SQL-completeness parser; a regression test covers comments and quoted semicolons. All four queries then executed, and SQL incoming degrees matched graph features for every transaction.

## Scientific checks

- 15 critical tests passed; see `tests.txt`.
- Seven notebooks executed from a fresh kernel each; execution metadata and outputs are retained.
- TreeSHAP contributions summed to model log-odds within tolerance.
- Named-attribute duplicate-fingerprint exclusion and complete-case sensitivity did not materially change the primary AP result.
- The shuffled-label control used one fixed seed and validation only. It is a diagnostic, not proof of leakage absence.
- Degree-only and component-excluded ablations were added after examining the main result. They are marked post-hoc and did not retune the final policy.
- Late-period collapse and the small incremental graph gain with extended local features remain central findings.

## Review scope

Tests were run locally. GitHub Actions configuration is supplied; remote CI execution is a separate observable status. PostgreSQL DDL is supplied but no PostgreSQL server execution is claimed. Native XGBoost TreeSHAP and SQLite were actually executed. A GNN, a Neo4j deployment, prospective business validation, and monetary-loss estimates were deliberately excluded from the completed scope.
