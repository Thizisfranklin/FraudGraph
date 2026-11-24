# FraudGraph — Regularization, Underfitting and Analyst-Capacity Research

> **Research phase, not deployment.** This extension was designed *after* observing performance degradation around step 43. Never describe later-period replay as an untouched generalization test. Fraud risk scores are not calibrated probabilities or accusations of wrongdoing.

## Research goals

The original graph-enhanced XGBoost model ranked known illicit transactions well in some periods and poorly in later periods. The [completed first drift experiment](https://github.com/Thizisfranklin/FraudGraph/actions/runs/45307007554) selected an expanding-history model with depth 3, 150 trees and learning rate .05 using earlier validation periods. Its AP improved in some previously inspected later periods but remained weak elsewhere.

The next controlled question is: **Can we reduce model complexity-related overfitting *and* avoid underfitting, while staying useful for a human analyst under realistic review limits?** This requires examining training-to-forward validation gaps, more than one model capacity, different presumed label delays, and analyst capacity.

## Model complexity & overfitting controls

`src/fraudgraph/robustness.py` compares four *prespecified* complexity presets on the same 15 named transaction attributes and eight engineered graph features:

| Preset | Depth | Trees | Min child weight | L2 lambda | L1 alpha | Row / column subsampling | Purpose |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| low_capacity | 2 | 90 | 12 | 12 | 1 | .80 / .80 | Detect possible underfitting with a constrained model |
| regularized | 3 | 150 | 10 | 12 | .5 | .80 / .80 | Reduce variance and improve generalization |
| reference_capacity | 3 | 150 | 5 | 5 | 0 | .90 / .90 | Compare to the previously strong temporal configuration |
| high_capacity | 5 | 280 | 2 | 2 | 0 | .95 / .95 | Detect whether extra model capacity boosts training but hurts future periods |

The XGBoost training settings are only hypotheses; no hyperparameter combination is guaranteed to improve test performance. We intentionally include both an underfit-leaning and an overfit-leaning configuration. Simpler does not always mean better.

We record **in-sample training Average Precision**, **future-bucket validation AP**, known-label prevalence for each, and the difference in AP above prevalence. Large train-versus-future gaps are signals for investigation, **not proof of ordinary overfitting**: actual temporal drift and selective label availability can also cause them.

### Why no automatic early stopping against the target bucket?

Doing so would let the future evaluation bucket influence tree count. That is exactly the kind of inadvertent look-ahead we want to prevent. This experiment instead compares fixed model capacity on **earlier validation folds**. Future work could use a strictly older *nested* early-stopping split inside each training window, without using its target bucket for either fitting or stopping.

## Temporal design and label-delay scenarios

- Keep the original task: **end-of-time-bucket transaction triage**, not instantaneous Bitcoin transaction authorization.
- Keep the original training history (1–29) for the frozen strategy.
- Run four strategies for each model preset: **frozen, expanding, rolling 15-bucket history, recency-weighted history**.
- For a target bucket `T` and label lag `L`, only train with **known labels** from buckets `<= T-L`. Unknown class 3 is **never** assumed licit.
- Evaluate all 16 candidate combinations on the same validation buckets **35, 37, 39** under each separate presumed label-delay scenario **L = 2, 4, 6**. These three windows were chosen so even the longest assumed delay can use the frozen original 1–29 history.
- **Choose one candidate per label-lag scenario on validation only**, by highest *worst-period* validation AP, then mean validation AP, then lower capacity. Worst-bucket AP is favored deliberately to discourage models that look impressive on average but collapse in a single period.
- Do **not** optimize which label delay to assume based on performance. Real label-maturation dates are absent in Elliptic++; the three lags are **availability scenarios**, not tunable knobs.
- The optional later replay on 40–49 is **post-hoc** because those periods influenced research design. It also assumes earlier test-period labels become available after `L` buckets—an assumption, not verified historical label arrival.

With only three validation periods, selection variance remains substantial. A genuinely independent later period is required for claims of robust generalization.

## Analyst workload evaluation

Using the model score, sort **every** transaction in each evaluated bucket, including unknown-label transactions. Allow analysts to review the top 1%, 5%, or 10%. Report:

- Total reviewed transactions (workload budget).
- Known illicit cases within the queue and fraction of **known illicit** transactions captured.
- Known licit cases placed in the review queue.
- Unknown-label cases that still consume analyst capacity.
- Lower/upper precision bounds if all unknown reviewed cases were licit versus illicit.

This is **triage**, not a fraud verdict. Known-illicit capture cannot be interpreted as true recall among all illicit transactions when the majority of outcomes are unknown. The system cannot estimate legal guilt, identity, customer harm or financial loss from these data.

## Run the research

Requires Python 3.12 and the original pinned Elliptic++ source data (about 700 MB). From the repository root:

```bash
pip install -r requirements.txt
pip install --no-deps -e .
python -m pytest -q
python -m fraudgraph.pipeline --download
python scripts/run_temporal_research.py
python scripts/run_robustness_research.py --label-lags 2 4 6
python scripts/build_research_dashboard.py
```

Only if you specifically want a retrospective replay on already-inspected steps:

```bash
python scripts/run_robustness_research.py --label-lags 2 4 6 --include-posthoc-test
python scripts/build_research_dashboard.py
```

Or run GitHub Actions → **Robustness and analyst research (manual)**, with post-hoc replay unchecked by default.

All outputs are saved to `reports/exploratory/` (Git-ignored):

| Filename | Content |
| --- | --- |
| `regularization_validation_folds.csv` | In-sample train AP, forward AP, prevalence, AP gaps, strategy and complexity for each validation period |
| `regularization_validation_leaderboard.csv` | Per-lag candidate rankings, worst/mean forward AP, AP gaps |
| `regularization_selected_per_lag.csv` | Explicit winner chosen separately within each label-lag scenario |
| `capacity_validation.csv` | Selected models: all-traffic analyst queues at 1/5/10% in validation |
| `regularization_posthoc_test.csv` | Only if opted in: retrospective steps 40–49 |
| `capacity_posthoc_test.csv` | Only if opted in: post-hoc analyst queue simulations |
| `regularization_manifest.json` | Experimental settings, provenance, interpretation warnings |
| `analyst_research_review.html` | **Interactive offline Plotly report**; open in a browser, no server or API needed |

The interactive HTML is an analyst-facing **research visualization** and **not** a deployed model or live external-wallet checker.

## What to review after the run

1. Compare simple versus complex models' train AP and forward AP (account for base rate).
2. Determine whether worst-fold forward AP improves as regularization strengthens.
3. Compare the *same evaluation periods* across the 2-, 4- and 6-bucket label-delay scenarios.
4. Assess known-illicit capture at a fixed analyst budget, not just AP.
5. Investigate how many reviewed transactions have unknown labels.
6. Verify that any apparent later-period gains persist on truly new time periods before changing production claims.

See [the analyst workbench roadmap](ANALYST_WORKBENCH_ROADMAP.md) for a future human-in-the-loop app design.
