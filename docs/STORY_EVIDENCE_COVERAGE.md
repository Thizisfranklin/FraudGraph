# Neon Ledger City — source-to-chapter coverage

The source tables and figures are not interchangeable. Their measurement populations and timestamps are preserved.

| Chapter | Research coverage | Exact evidence |
| --- | --- | --- |
| 0 Entrance | The motivating question; analyst-not-verdict framing | README.md, docs/UNDERSTAND_AND_CHECK.md |
| 1 One Transaction | Class labels, imbalance, anonymization, 15 named intrinsic features, missingness, chronology | reports/data_validation.json, reports/splits.csv, reports/FEATURE_DICTIONARY.md, reports/LEAKAGE_AUDIT.md |
| 2 The Network | Directed nodes and edges, per-bucket components, degrees, PageRank, feature availability, SQL parity | reports/graph_validation.json, reports/graph_feature_summary.csv, reports/EXECUTION_NOTES.md |
| 3 The Uplift | Original saved case scores and explanation provenance, contrast with known licit | reports/cases.csv, reports/case_shap_logodds.csv |
| 4 It Depends | Full eight primary models, pooled test AP, named versus 93 anonymous locals, logistic negatives, paired bootstrap, validation reliance | reports/results.csv, reports/paired_comparison.json, reports/permutation_importance.csv |
| 5 The Analyst Queue | All-traffic Top-K budgets, known vs unknown, distinct fixed risk bands and friction limits | reports/review_capacity.csv, reports/DECISION_FRAMEWORK.md, reports/decision_policy.json |
| 6 The Plot Twist | Original chronological AP, early/later cohorts, label prevalence and small sample counts | reports/test_by_time.csv, reports/robustness.csv, reports/class_by_time.csv |
| 7 Why Did It Break? | PSI/Wasserstein, score shift, missingness, component signatures, conditional drift uncertainty | temporal Actions: feature_drift_by_time.csv, label_score_drift_by_time.csv; docs/BASELINE_TEMPORAL_FINDINGS.md |
| 8 Retraining Loop | Frozen, expanding, rolling, recency weighting, validation-only selection, previously inspected test replay clearly marked, unsupported combos placeholder | temporal Actions: adaptive_validation_folds.csv, adaptive_validation_leaderboard.csv, adaptive_posthoc_test_by_time.csv |
| 9 Stress Tests | Model complexity/regularization, train-versus-forward AP, three hypothetical label delays, worst-fold selection and possible under/overfitting | robustness Actions: regularization_validation_folds.csv, regularization_validation_leaderboard.csv, regularization_selected_per_lag.csv |
| 10 Analyst Budgets | Three selected validation candidates, 1/5/10% actual review capacities, unknowns consume analyst time | robustness Actions: capacity_validation.csv |
| 11 Workbench | Existing React case review, 101 real source-backed example networks, analyst disposition, actual product versus roadmap | app/public/investigations.json, app/README.md, docs/ANALYST_WORKBENCH_ROADMAP.md |
| 12 Takeaway | Negative control, source hashes, 7 executed notebooks plus unexecuted eighth, reproducibility, leakage, SQL, TreeSHAP, duplicates, no prospective efficacy | reports/EXECUTION_NOTES.md, reports/artifact_verification.json, reports/negative_control.json, reports/duplicate_audit.json, docs/UNDERSTAND_AND_CHECK.md |

## Additional evidence drawer

The always-accessible Evidence Vault links to the dataset audit, feature dictionary, leakage audit, model comparisons, paired-bootstrap uncertainty, negative controls, duplicate and complete-case sensitivity, threshold versus queue policy, chronological failure, temporal experiments, robustness experiments, engineering execution notes, and existing investigator roadmap.

## What remains unproven, not hidden

- A verified cause of the collapse / confirmed concept drift.
- Actual label-maturation timestamps for the hypothetical delay scenarios.
- Genuinely unseen post-study future fraud labels to confirm generalization.
- Recoveries, monetary harm, customer-level fraud outcomes, or real-world false-positive burden.
- Arbitrary live Bitcoin wallet/TXID scoring, calibration, or a safe production investigation service.
- Capacity outcomes for combinations not recorded by the experiment. Play mode displays the exact missing-data placeholder.

**All chapters implemented.** No supported findings remain deliberately omitted from the planned chapter coverage. Specific unsupported outcomes above remain labeled as missing.
