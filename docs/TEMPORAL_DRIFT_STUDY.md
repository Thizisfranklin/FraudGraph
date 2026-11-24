# FraudGraph — Drift and Temporal Adaptation Study

> **Exploratory extension:** The original main-branch experiments, CSVs and claims remain unchanged. The temporal test-period collapse was known before this extension was designed. Any comparisons on those later periods are **post-hoc** and cannot be called fresh out-of-sample confirmation.

## Question

Why did the named-attribute XGBoost + graph model show strong ranking in some test buckets but nearly random ranking in later buckets? Can time-aware training improve *robustness*, not just the pooled score?

The current reports show **time-step 43** as the visible start of an abrupt drop, not simply the boundary between 40–43 and 44–49. Known-illicit prevalence also changes. AP must always be read alongside the known-label prevalence and sample size.

## Changes in this branch

- `src/fraudgraph/drift.py`: PSI against a historical reference, Wasserstein distances, missingness, known-label prevalence/coverage, score distribution, per-bucket AP and AP minus prevalence.
- `src/fraudgraph/adaptation.py`: frozen-history, expanding-history, rolling-window and exponentially recency-weighted XGBoost; strict label-delay indexing; validation-only strategy/hyperparameter selection; controlled graph feature ablations.
- `scripts/run_temporal_research.py`: saves CSV evidence and a method manifest without overwriting original reports.
- `notebooks/08_temporal_drift.ipynb`: visualization and discussion starter.
- `tests/test_drift.py` and `tests/test_adaptation.py`: synthetic unit tests for unknown outcomes, drift calculations and temporal boundaries.

## Reproduction

Install the project's dependencies in Python 3.12 and prepare the existing original outputs:

```bash
pip install -r requirements.txt
pip install --no-deps -e .
python -m pytest -q
python -m fraudgraph.pipeline --download
python scripts/run_temporal_research.py
```

The first research run produces **validation** and historical drift/ablation evidence, but deliberately omits the already-observed test-period replay until explicitly requested:

```bash
python scripts/run_temporal_research.py --include-posthoc-test --label-lag 2
```

The run creates `reports/exploratory/` containing:

| Output | What it measures |
| --- | --- |
| `feature_drift_by_time.csv` | PSI, Wasserstein, missingness, historical vs current medians |
| `label_score_drift_by_time.csv` | Label coverage, known illicit prevalence, score quantiles, original-model AP |
| `graph_ablation_by_time.csv` | Frozen XGBoost with reduced graph feature sets or without transaction size, by bucket |
| `adaptive_validation_folds.csv` | Every proposed strategy/hyperparameter setting on validation-only forward folds |
| `adaptive_validation_leaderboard.csv` | Mean validation AP, worst-fold AP, and AP above prevalence |
| `adaptive_posthoc_test_by_time.csv` | **Only with flag:** selected adaptive model's retrospective test-step AP |
| `selection_manifest.json` | Model settings, assumptions, warning that the test data was previously inspected |

These are generated artifacts, not included in Git unless regenerated.

## Experimental design

- **Prediction contract:** Batch scoring at the **end** of each time bucket. Edges and attributes within the current bucket are assumed available, but the bucket's labels are not.
- **Original main experiment:** Train 1–29, validation 30–39, test 40–49. Preserve its scores and plots as-is.
- **New validation folds:** 31, 33, 35, 37, 39. A fold at target step `T` can train only on **known labels from steps <= T - label_lag**. The frozen model trains on steps 1–29. Validation is used to choose the retraining strategy and XGBoost settings.
- **Training strategies:** Frozen; expanding labeled history; last 15 eligible steps; exponentially decayed weights (eight-step half-life). The same 15 named attributes and eight engineered graph columns are used to compare the strategies.
- **Hyperparameter candidates:** Max depth 3 / 4 / 5, tree count 150 / 250 and learning rate .03 / .05 in a fixed 3-combination budget applied to each strategy. All other XGBoost settings remain aligned to the original project.
- **Test replay (opt-in):** Evaluation on 40–49 uses the validation-selected candidate. As time advances, the model may train on earlier test-bucket **labels** only once the assumed delay has elapsed. This is *not* a frozen original holdout evaluation.
- **Graph ablations:** Compare transaction only, degrees only, all nonconstant graph features, without component features, and without the heavily relied-upon transaction `size`. These were chosen after inspecting results and must be labeled exploratory.
- **Label handling:** Unknown class 3 remains unlabeled; no treating unknown transactions as negatives. Unlabeled data participates in topology and unsupervised drift calculations.
- **Metric:** AP per bucket, number of labeled transactions, known illicit count, known-label prevalence, and AP minus prevalence. Avoid averaging away difficult later periods.

## What is, and is not, drift evidence?

- **Observed performance degradation:** Per-time-bucket AP drops substantially. This is proven by saved labeled evaluation metrics.
- **Observed known-label prevalence change:** The proportion labeled illicit changes over time. This may reflect underlying class priors, selective label availability, or both.
- **Input drift:** PSI and Wasserstein characterize changes in feature distributions; they do not identify why those distributions changed.
- **Prediction drift:** Score quantiles can change even when the underlying concept remains fixed.
- **Concept drift:** A change in `P(label | features)` is plausible but not established by these data alone. Label selection/maturation and changing transaction populations complicate inference.

Pay special attention to **transaction `size`**: the earlier permutation importance showed a very large validation AP decrease when it was permuted. Investigate how its predictive relationship changes around step 43. Also note that all observed edges connect nodes inside the same time bucket, so `g_component_size` and `g_component_density` may reveal cohort signatures. Ablation results must be evaluated across buckets, not pooled alone.

## What would count as a credible improvement?

1. Better average AP **and** better worst-period AP across multiple forward validations.
2. Better capture of known illicit activity under a fixed analyst budget, including unknown-label transactions in traffic volume.
3. No dependence on labels or features that were unavailable at decision time.
4. An untouched later dataset (or truly prospective data) for final validation **after** we finish studying the 40–49 collapse.

We have **no verified label-maturation dates**. The `--label-lag 2` default is a scenario, not documented source truth. Report sensitivity to longer lags before making deployment claims. There is currently no empirical claim that this extension improved performance; run the experiments first and report both wins and failures.

## Review checklist and follow-up

- Check constant / bucket-signature graph features.
- Check that decision-time availability of out-degree and PageRank fits batch scoring.
- Check missingness separately for illicit, licit and unknown.
- Check that drift metrics use historical bins and exclude outcome labels from the comparison.
- Check that validation-only candidate selection precedes test replay.
- Verify how different assumed label lags affect outcomes.
- Add rolling threshold/capacity assessments if ranking improves.
- Seek truly unseen later data before describing any solution as drift-resistant.
