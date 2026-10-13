# FraudGraph investigation explorer

A **read-only Streamlit viewer** of the project's *committed* evaluation
artifacts. It adds interactivity without replacing the notebooks or claiming a
live fraud-detection system.

## Run locally

From the repository root, with **Python 3.12**:

```bash
python -m pip install -r requirements-explorer.txt
python -m streamlit run explorer.py
```

No original data download, graph computation, trained model, API token or GPU is
needed to explore the saved results. The viewer reads only:

- `reports/results.csv`: held-out average precision across model pairs
- `reports/review_capacity.csv`: top-K review outcomes at five budget levels
- `reports/test_by_time.csv`: time-bucket average precision and known prevalence
- `reports/cases.csv`: three **selected illustrative** cases

The case diagram is a saved figure; visitors cannot type arbitrary transaction
IDs or generate a new prediction in this demo. Scores are uncalibrated model
outputs, **not** probabilities that a person committed a crime.

## Reading the displays

**Model comparison** shows held-out *Average Precision* (AP) over known
illicit/licit labels only. The transaction-only and graph variants have the
same chronological splits and learner configuration. This does not measure
accuracy on unknown-label transactions.

**Analyst workload** uses the **all-transaction top-K per time bucket** results.
Unknown-label transactions consume reviewer capacity. The known-illicit
capture rate is conditional on observed labels, *not* real-world recall or
profit. Switching the budget only looks up five precomputed budgets; it does
not change the model or optimize staffing costs. This differs from the separate
fixed-score risk bands in `reports/DECISION_FRAMEWORK.md`.

**Temporal reliability** highlights that pooled AP hides large variations
across the 10 held-out time buckets. Known illicit prevalence also changes,
so differences in AP are not evidence for one specific drift mechanism.

**Selected cases** are illustrative and not a representative model audit.
Their neighboring graph is only available as the saved case-study image; no
live full graph, identity inference, or wallet ownership is reconstructed.

## What this is not

Not a live blockchain feed, risk API, case-management system, calibrated
probability estimator, production fraud filter, or new scientific evaluation.
For the prediction-time contract and limitations, see
[`reports/LEAKAGE_AUDIT.md`](../reports/LEAKAGE_AUDIT.md) and
[`docs/UNDERSTAND_AND_CHECK.md`](UNDERSTAND_AND_CHECK.md).

## Checks

```bash
python -m pytest -q tests/test_explorer.py
```

The checks verify required report fields, select committed model and capacity
rows, and reconcile known/unknown reviewer counts. They do not replace the
original pipeline methodology tests.
