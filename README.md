# FraudGraph

**Can a Bitcoin transaction look ordinary on its own—but different once you follow its connections?**

FraudGraph is my **independent machine learning research project** exploring whether graph features improve transaction risk ranking—and whether those improvements hold up over time. It uses the [Elliptic++ Bitcoin transaction dataset](https://github.com/git-disl/EllipticPlusPlus), not live blockchain queries.

I've always been curious about Bitcoin. When I wanted to build a fraud-detection project, I decided to move beyond the familiar credit-card fraud datasets and challenge myself with something harder: **connected transactions, incomplete labels, and models that can fail when the data changes**.

## Two ways to explore the same research

<table>
<tr>
<td width="50%" valign="top">
<a href="https://thizisfranklin.github.io/FraudGraph/investigator/"><img src="https://image.thum.io/get/width/800/crop/560/https://thizisfranklin.github.io/FraudGraph/investigator/" alt="FraudGraph Investigator landing page: dark professional transaction review workspace" width="100%"></a>
<h3>FraudGraph Investigator</h3>
<strong>The practical analyst workspace.</strong><p>Review 101 saved Elliptic++ transaction cases, inspect their network relationships, compare historical model scores, and record case notes.</p>
<a href="https://thizisfranklin.github.io/FraudGraph/investigator/"><strong>Open Investigator →</strong></a>
</td>
<td width="50%" valign="top">
<a href="https://thizisfranklin.github.io/FraudGraph/"><img src="https://image.thum.io/get/width/800/crop/560/https://thizisfranklin.github.io/FraudGraph/" alt="Neon Ledger City landing page: colorful neon-city research story" width="100%"></a>
<h3>Neon Ledger City</h3>
<strong>The cinematic interactive story.</strong><p>Explore the same evidence through a retro-city visual experience inspired by the atmosphere of <em>Grand Theft Auto</em>. The interface and artwork are original; no game assets or branding are used.</p>
<a href="https://thizisfranklin.github.io/FraudGraph/"><strong>Enter Neon Ledger City →</strong></a>
</td>
</tr>
</table>

*Same underlying experiments, two different experiences. Both are offline historical research prototypes—not live wallet checkers or automatic fraud-verdict systems.*

## What I investigated

**203,769 transactions · 234,355 directed links · 49 time steps**

I built graph features and compared transaction-only against transaction + graph models using **chronological splits**: train on steps **1–29**, validate on **30–39**, test on **40–49**. I kept unlabeled transactions **unknown**, never silently treating them as legitimate.

### 1. Does graph context help?

<p align="center"><img src="reports/figures/model_comparison.png" alt="Recorded held-out model-comparison and analyst review-capacity results" width="850"></p>

With **15 named transaction attributes**, XGBoost test Average Precision (AP) rose from **0.4239 to 0.5240** after adding graph features. With **93 additional local attributes**, the increase was much smaller: **0.6349 to 0.6398**. At a review capacity of **5% of all test transactions**, the selected model surfaced **273 of 636 known-illicit test transactions (42.9%)**.

### 2. What happens when time moves forward?

<p align="center"><img src="reports/figures/temporal_generalization.png" alt="Observed temporal performance degradation in the original model" width="850"></p>

The primary graph model's AP dropped from **0.7070 to 0.0257** when comparing earlier and later test periods. Follow-up drift, retraining, and robustness experiments investigated this weakness, but they do **not** establish its cause or prove prospective deployment reliability.

**The takeaway:** a strong aggregate metric does not guarantee a reliable model tomorrow.

> **Important:** AP measures ranking quality on transactions with *known* dataset labels; it is not accuracy, money recovered, or criminal guilt. “Illicit” is the dataset's retrospective transaction label, not a verdict about a person. Scores are uncalibrated.

## Code and reproducibility

[Research notebooks](notebooks/) · [Reports and figures](reports/) · [Leakage audit](reports/LEAKAGE_AUDIT.md) · [Methods and limitations](docs/UNDERSTAND_AND_CHECK.md) · [Robustness study](docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md)

**Tools:** Python, pandas, NetworkX, SQL/SQLite, scikit-learn, XGBoost, matplotlib, Plotly, pytest; React, TypeScript, Vite, React Flow, and Framer Motion.

*Original dataset: [Elliptic++](https://github.com/git-disl/EllipticPlusPlus) (Elmougy & Liu, 2023). App preview images are automatically generated from the linked live pages.*
