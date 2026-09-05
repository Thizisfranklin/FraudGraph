# FraudGraph — Fraud, Risk & Customer Trust 

> A graph-based fraud analytics project investigating whether relationships between transactions, payment attributes, devices, and customer identity signals can improve fraud detection while reducing unnecessary friction for legitimate users.

## Context

Online platforms must make fraud decisions quickly.

If fraud controls are too weak, the company may experience:

* financial losses
* chargebacks
* abuse
* account compromise

But fraud controls can also be too aggressive.

A legitimate customer may experience:

* a declined payment
* additional verification
* an account restriction
* a delayed purchase
* a manual review

The business problem is therefore not simply:

> **How much fraud can we detect?**

It is:

> **How much fraud can we detect without creating unnecessary friction for legitimate customers?**

---

## 1. Business Questions

### A. Can relational information improve fraud detection?

Individual transactions may look legitimate on their own.

Fraud can become more visible when relationships are considered.

Examples:

```text
Transaction → Payment Card
Transaction → Device
Transaction → Email Domain
Transaction → Address
Transaction → Identity Signal
```

The project investigates whether graph-derived features improve detection beyond transaction-level models.

### B. What threshold should trigger intervention?

A lower risk threshold may catch more fraud but incorrectly flag more legitimate transactions.

A higher threshold may improve customer experience but allow additional fraud.

The final decision therefore considers:

**fraud capture + false positives + review workload**

rather than model accuracy alone.

---

## 2. Scope

Version 1 focuses on **online payment fraud**.

It will not attempt to:

* detect every type of financial crime
* build a real banking fraud platform
* claim that false positives directly cause customer churn
* model every possible graph neural network
* build a real-time production streaming system

The goal is a defensible offline fraud and intervention analysis.

---

## 3. Data

### Primary Candidate — IEEE-CIS Fraud Detection

The dataset contains transaction and identity information joined through `TransactionID`.

Useful information includes:

* transaction amount
* product
* payment-card attributes
* address attributes
* email domains
* device information
* behavioral/identity signals
* fraud label

Some variables are intentionally anonymized.

The project will not invent meanings for masked variables.

---

## 4. Graph Construction

Possible node/entity types:

```text
Transaction
Card
Device
Email Domain
Address
```

Possible relationships:

```text
Transaction --USED--> Card
Transaction --FROM_DEVICE--> Device
Transaction --EMAIL--> Email Domain
Transaction --ADDRESS--> Address
```

This allows the system to detect patterns that may not be obvious from one transaction at a time.

Example:

```text
Card A
  |
Transaction 1 ---- Device X
                    |
Transaction 2 ---- Card B
                    |
Transaction 3 ---- Card C
```

Three transactions that appear unrelated may actually share the same device.

---

## 5. Modeling

Keep the comparison simple.

### Baseline

**Logistic Regression**

### Traditional ML

**XGBoost**

### Graph-Enhanced ML

**XGBoost + graph features**

Candidate graph features:

* degree
* number of shared devices
* number of shared payment entities
* connected-component size
* centrality
* neighborhood fraud rate

### Optional Extension

If time permits:

**GraphSAGE or another GNN**

Deep learning is a stretch goal, not a requirement for completing the project.

---

## 6. Evaluation

Fraud is highly imbalanced, so accuracy will not be the main metric.

Evaluate with:

* PR-AUC
* precision
* recall
* false-positive rate
* recall at fixed false-positive rate
* Precision@K

The main technical question is:

> **Do graph relationships improve fraud detection compared with transaction-only features?**

---

## 7. Customer-Friction Analysis

Model thresholds will also be interpreted as product decisions.

For each threshold measure:

```text
Fraud detected
Fraud missed
Legitimate transactions flagged
Transactions sent to review
```

Example decision:

```text
Threshold A:
Higher fraud recall
Higher legitimate-user interruption

Threshold B:
Slightly lower fraud recall
Substantially fewer false positives
```

The recommended threshold should balance:

**risk protection** and **customer experience**.

---

## 8. Trust & Retention

The available fraud dataset does not directly measure customer trust or retention.

Therefore, the project will not claim:

> "The model increased retention."

Instead, false-positive interventions will be treated as measurable **customer-friction proxies**.

A production system should later measure whether intervention policies affect:

* repeat transactions
* account abandonment
* customer-support contacts
* verification completion
* appeal/reversal rates
* retention

---

## 9. Dashboard

A compact Trust & Safety dashboard can show:

### Model Performance

* fraud recall
* precision
* PR-AUC

### Policy Simulator

Adjust the risk threshold and observe:

* fraud caught
* legitimate users flagged
* review volume

### Graph Investigation

Explore suspicious connected entities and fraud clusters.

---

## 10. Business Recommendation

> Added after analysis.

The final recommendation should answer:

1. Do graph features materially improve fraud detection?
2. Which relationships are most useful?
3. What threshold produces the best fraud/customer-friction trade-off?
4. How much manual review does the policy create?
5. What user-experience metrics should be monitored after deployment?

---

## 11. Limitations

Known limitations:

* several IEEE-CIS variables are anonymized
* offline data does not directly measure customer trust
* false positives are proxies for user friction, not retention itself
* fraud behavior evolves over time
* model thresholds depend on the business cost of fraud versus legitimate-user interruption

---

## 12. Technology Stack

**Data:** Python, SQL, pandas
**Graph Analytics:** NetworkX, Neo4j
**Machine Learning:** scikit-learn, XGBoost
**Optional Deep Learning:** PyTorch Geometric
**Visualization:** Plotly / Streamlit
**Development:** Git, GitHub, Jupyter

---

## 13. Repository Structure

```text
fraudgraph/
│
├── README.md
├── data/
│   └── README.md
├── notebooks/
│   ├── 01_data_validation.ipynb
│   ├── 02_fraud_eda.ipynb
│   ├── 03_graph_construction.ipynb
│   ├── 04_baseline_models.ipynb
│   ├── 05_graph_models.ipynb
│   └── 06_threshold_analysis.ipynb
├── sql/
├── src/
├── dashboard/
├── reports/
├── requirements.txt
└── .gitignore
```

---

## 14. Results

> To be completed after analysis.

No hypothetical fraud, customer-friction, or retention improvements will be presented as actual results.
