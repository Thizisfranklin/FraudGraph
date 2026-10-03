# Understand and check FraudGraph

A short guide to the questions I would need to answer if I were presenting this project in an interview. Start with the *why*; use the linked files to verify the *how*.

## 1. What problem was I trying to solve?

A transaction's own attributes might not tell a financial-crime investigator enough. Its relationships to other observed transactions might provide additional information. The project tests **whether graph features improve ranking of known illicit transactions** relative to equivalent transaction-only models.

This is *prioritization*, not proof of wrongdoing or an automated fraud-blocking product. A suspicious score isn't a calibrated probability of a crime.

## 2. What is a graph?

Each **node is a Bitcoin transaction**. A directed **edge links transactions that have a documented money-flow relationship** in Elliptic++. This is not a wallet-owner or customer-device graph: the transaction data can't justify claims about unique people, shared devices or established account ownership.

Features describe the network at the end of each time step: in-degree, out-degree, PageRank, component size/density and nearby transactions' degrees. The project builds those features from visible transactions and edges at each cutoff. [Feature dictionary](../reports/FEATURE_DICTIONARY.md).

For an example, study [the selected neighborhood image](../reports/figures/case_graph_uplift.png) and then [the saved case record](../reports/cases.csv). One score rises when graph context is added, but a handpicked illustrative case doesn't prove the overall result.

## 3. Why not randomly split the data?

If future relationships influence the features of transactions we pretend to score in the past, the evaluation becomes unrealistic. FraudGraph trains on time steps **1–29**, selects models and thresholds on **30–39**, and tests on **40–49**.

There is an important qualification: **end-of-bucket** graph context is assumed available. An out-degree feature might not be visible at the instant an individual transaction occurs. This experiment therefore models batch review at bucket close, not an instantaneous live alert. Read [the leakage audit](../reports/LEAKAGE_AUDIT.md).

The majority of labels are **unknown**, not negative. Unknown nodes can be used for graph topology, but they aren't used as labeled legitimate examples when fitting or calculating standard precision/recall.

## 4. What models were compared?

The central experiment compares the **same XGBoost learner** with (a) 15 interpretable transaction attributes alone and (b) those same attributes plus engineered graph features. Logistic regression provides another learner comparison.

Then a **sensitivity experiment** repeats the comparison after adding 93 anonymous local transaction attributes to both alternatives. These extra columns have incomplete interpretability and are not evidence that additional named real-world financial variables were independently collected.

At the final chronological test split:

| Experiment | Transaction-only AP | Transaction + graph AP |
| --- | ---: | ---: |
| XGBoost with named attributes | 0.4239 | 0.5240 |
| Logistic regression with named attributes | 0.0906 | 0.0696 |
| XGBoost with extended local attributes | 0.6349 | 0.6398 |

This is why “graph features always improve fraud detection” would be incorrect. Results vary by learner and the information already available. The paired time-bucket bootstrap for the main XGBoost AP difference is approximately **+0.100**, with a 95% interval **+0.002 to +0.137**, but only ten test time buckets limit generalization. See [paired comparisons](../reports/paired_comparison.json).

## 5. What is Average Precision, and why use it?

When the illicit class is rare, accuracy can look high even if the model rarely identifies illicit transactions. **Average Precision (AP)** summarizes the precision–recall ranking curve across thresholds *on the known-label evaluation population*.

It does not prove accurate probabilities, characterize transactions with missing labels, or tell a risk team how many investigations its staff can manage.

## 6. How was the analyst-budget result calculated?

The review-capacity analysis sorts **all transactions** in each time bucket, including those without labels, by model score. It then takes the top K within each bucket. This is distinct from the fixed-score LOW/REVIEW/HIGH banding system.

For the selected `named_xgboost_graph` model on the test set and a **5% all-traffic budget**: the saved report records **2,337 transactions selected for review**, with **273 known illicit**, **140 known licit** and **1,924 unknown** labels. There were **636 known illicit** transactions in the labeled test group, so **273 / 636 = 42.9% of known illicit cases**.

Do not say the model caught 42.9% of *all real illicit activity*. Most traffic has no ground-truth label. Also don't interpret the fixed-score band boundaries as an enforceable 5% workload cap; the per-time-bucket top-K policy enforces that capacity assumption. [Decision policy](../reports/DECISION_FRAMEWORK.md).

## 7. What failed when testing later periods?

For the primary named-attribute XGBoost + graph model, AP was **0.7070** in early test steps **40–43**, then **0.0257** in later steps **44–49**. The underlying prevalence also changes, so this is evidence of substantial instability, *not proof of one specific cause*. It matters more for deployment decisions than displaying the pooled AP alone. See [saved cohort results](../reports/robustness.csv) and [temporal visual](../reports/figures/temporal_generalization.png).

## 8. How do I verify that the numbers aren't just prose?

The repository preserves the executed figures, a [results table](../reports/results.csv), [review-capacity rows](../reports/review_capacity.csv), [source and code hashes](../reports/run_manifest.json), and the [artifact verification summary](../reports/artifact_verification.json).

In a Python 3.12 environment, install requirements and the package, then run `python -m pytest -q`. This runs the **15 critical methodology tests**. To regenerate the full results, run `python -m fraudgraph.pipeline --download`, then diagnostics, notebook/report builders and finally `python scripts/verify_artifacts.py`. The source download is large; the verifier requires generated artifacts, including held-out predictions, so don't run it expecting a clean clone without reproducing those files first.

A passing software test establishes that its assertions held. It doesn't prove the dataset's labels are perfectly representative or establish operational usefulness without a prospective trial.

## 9. What would I do differently in a real investigation team?

Clarify when every feature becomes available, obtain label-maturation dates and more representative outcomes, quantify analyst effort and error cost, evaluate performance across newer periods, and pilot any prioritization rule prospectively. Only then consider drift alerts, calibrated risk scores or a user-facing product.

**Five-minute interview structure:** problem → transaction versus network idea → why chronological evaluation → primary result and sensitivity test → why later-period deterioration changed the conclusion. Don't memorize an impressive AP number without being able to explain what it measures and who is excluded.
