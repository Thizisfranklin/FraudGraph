# FraudGraph: What the saved results actually establish

This report summarizes **existing**, previously run project results; it does **not** report new retraining outcomes. Sources: [per-time AP](../reports/test_by_time.csv), [robustness cohorts](../reports/robustness.csv), [label counts](../reports/class_by_time.csv), and [feature importance](../reports/permutation_importance.csv).

## An abrupt change near time step 43

The collapse is not restricted to the graph-enhanced model. Transaction-only and graph-enhanced XGBoost models both weaken sharply when evaluated on known labels from step 43:

| Existing model | AP step 42 | AP step 43 |
| --- | ---: | ---: |
| named_xgboost_tx | 0.7247 | 0.0268 |
| named_xgboost_graph | 0.8142 | 0.0265 |
| extended_xgboost_tx | 0.8750 | 0.0382 |
| extended_xgboost_graph | 0.8786 | 0.0372 |

### Per-bucket context for the primary graph XGBoost

| Time step | Known illicit / labeled | Known-illicit fraction | AP | AP minus known prevalence |
| ---: | ---: | ---: | ---: | ---: |
| 40 | 112 / 1211 | 9.25% | 0.5552 | 0.4627 |
| 41 | 116 / 1132 | 10.25% | 0.8412 | 0.7388 |
| 42 | 239 / 2154 | 11.10% | 0.8142 | 0.7033 |
| 43 | 24 / 1370 | 1.75% | 0.0265 | 0.0090 |
| 44 | 24 / 1591 | 1.51% | 0.0257 | 0.0106 |
| 45 | 5 / 1221 | 0.41% | 0.0092 | 0.0051 |
| 46 | 2 / 712 | 0.28% | 0.0235 | 0.0207 |
| 47 | 22 / 846 | 2.60% | 0.0245 | -0.0015 |
| 48 | 36 / 471 | 7.64% | 0.1101 | 0.0336 |
| 49 | 56 / 476 | 11.76% | 0.1048 | -0.0129 |

**Interpretation:** The sudden deterioration at step 43 coincides with a sharp drop in known-illicit prevalence, from **11.10%** at step 42 to **1.75%** at step 43. The ranking AP of multiple model families also deteriorates. This is evidence of **model performance degradation** and a substantial change in labeled-population composition; it does **not** alone identify concept drift.

## Other existing evidence that matters

- The [validation permutation-importance table](../reports/permutation_importance.csv) gives transaction `size` by far the largest estimated impact (mean AP drop **0.5731**) when shuffled on known validation labels. This motivates a feature-by-time relationship study, not a conclusion of leakage or causality.
- The [graph feature summary](../reports/graph_feature_summary.csv) reports exactly **49** unique values of both component size and component density, while the [graph validation](../reports/graph_validation.json) reports **49** weak components and all original edges are within time steps. These features may encode bucket identifiers or dataset-cohort properties.
- Existing [post-hoc ablations](../reports/structural_ablations.csv) reported AP **0.5240** with all graph features versus **0.5057** without component features and **0.4683** with degree-only features. Those are pooled labeled test scores, which can mask period-specific degradation.
- The main [leakage audit](../reports/LEAKAGE_AUDIT.md) explicitly defines **end-of-time-bucket** scoring, unknown-label handling, and the absence of source label-maturation timestamps. Keep these assumptions for all new experiments.

## What we cannot conclude yet

1. We cannot attribute the step-43 drop solely to the graph, because transaction-only models also deteriorated.
2. We cannot attribute it solely to changes in the illicit base rate: AP changes with prevalence, but poor rankings may also indicate feature or conditional-label shift.
3. We cannot claim confirmed concept drift (`P(Y|X)` changed) without more robust evidence about feature relationships and label selection.
4. We cannot claim new adaptive models are better before the exploratory scripts run, and any improvement on steps 40–49 is **post-hoc** because we already investigated those steps.

## Next tests

Run [the temporal drift script](../scripts/run_temporal_research.py) after restoring the original processed Parquet files; inspect feature drift, scores, ablations, and validation-only adaptive selection. The [study protocol](TEMPORAL_DRIFT_STUDY.md) explains the limits and the explicit two-bucket label-delay assumption. A **genuinely unseen future period** is necessary for a credible final generalization claim.
