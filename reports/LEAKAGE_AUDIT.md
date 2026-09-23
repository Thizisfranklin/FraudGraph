# Leakage and prediction-time audit

## Prediction contract

The prediction unit is a Bitcoin transaction. The target is the dataset's known illicit label, not a proven legal conclusion or a chargeback outcome. Scores are computed at the **end of the transaction's time bucket**. All transactions and observed edges in that bucket are assumed available; labels in that bucket are unavailable. This is batch retrospective risk triage, not instantaneous authorization.

The dataset has 49 coarse time steps and no sufficient per-edge arrival timestamps for an honest within-step online replay. Out-degree, components, and PageRank can contain information that would arrive after the individual transaction but before bucket close. They pass the stated batch contract only. Do not describe the results as real-time detection.

## Split and fitting

- Train: steps 1–29. Validation: 30–39. Test: 40–49.
- Boundaries and the eight model/feature combinations were chosen before seeing model results.
- ID sets are disjoint. No random row split and no target encoding.
- Unknown class 3 maps to a missing outcome, never to legitimate class 0.
- Imputation and scaling fit on known-label training rows only, within sklearn pipelines.
- Validation chooses an F1 threshold per model and the operational model by average precision. Test results do not select hyperparameters, policy model, or thresholds.
- Both graph and transaction versions use identical splits, learner hyperparameters, label handling, and threshold-selection procedures.
- No early stopping or large search; 250 boosted trees and one logistic specification per feature set. Logistic uses balanced class weights; XGBoost uses unweighted log loss. Scores are not calibrated probabilities.

## Feature provenance

The primary baseline uses only 15 named intrinsic transaction attributes: value, fees, bytes, address counts, and distributions of input/output BTC amounts. The names support transaction-level interpretation, but the source's exact extraction code is not supplied here and cannot be independently reconstructed from anonymized IDs.

The primary baseline excludes the 93 anonymized local columns, 72 supplied aggregate columns, supplied in/out graph degrees, transaction ID, time-step index, and labels. A separately labeled sensitivity experiment adds the 93 local columns to both arms. Their source normalization and exact availability are not fully auditable; sensitivity results are not stronger production-validity evidence than the primary experiment.

Graph features are recomputed from visible nodes and edges for each cutoff, using no labels and no supplied aggregate features. Unknown nodes participate in topology because their edges are observable, not because their class is inferred. Each row is frozen at its own cutoff. There is no full-future graph computation followed by a split.

## Automated checks and evidence

`tests/test_graph.py` perturbs future nodes/edges and labels and verifies that past features remain unchanged. It checks degree orientation, components, isolates, and ID alignment. `tests/test_data.py` rejects duplicate IDs, dangling endpoints, and inconsistent embedded targets; it verifies unknown-label handling. `tests/test_evaluation.py` checks temporal boundaries, tie handling, review capacity, thresholds, and confusion counts.

`data_validation.json` records IDs, missing values, labels, time edges, file hashes, and schema checks. `duplicate_audit.json` records identical named-feature fingerprints shared across splits. Equal values on distinct IDs do not demonstrate duplicate transactions; they can represent ordinary repeated transaction patterns. All-missing attribute rows also share fingerprints. They remain in the primary population, with a separate robustness analysis excluding test fingerprints seen in training. Unknown outcome missingness is not assumed random.

## Residual risks

All observed edges are within a time bucket. Thus the holdout tests later disconnected graph populations, not connected historical propagation. Entity-level duplication cannot be ruled out without usable wallet identity. Labels may have been assigned using evidence obtained after the nominal time step; label availability dates are absent. The experiment assumes training outcomes are mature by fitting time. Dataset construction and selective labeling can inflate apparent performance relative to deployment.

There are only ten test time buckets. A paired time-bucket bootstrap is a descriptive uncertainty estimate, not proof across independent markets. Temporal dependence between buckets and large regime shifts limit its interpretation. Inspect `test_by_time.csv`, rather than relying on pooled AP alone. The unknown population prevents identification of true population precision, recall, or false-positive rates. Capacity reports show known outcomes and precision bounds on all traffic.
