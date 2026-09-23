# Risk triage and customer friction

These are risk scores for an analyst workflow, not calibrated fraud probabilities or automatic grounds to block a customer.

1. Select the primary model with highest validation AP, before examining test performance.
2. Set the LOW/REVIEW boundary to the 95th percentile of scores on **all** validation transactions. A 5% review fraction is an explicit illustrative staffing scenario, not an estimated business optimum.
3. Among score thresholds at or above that boundary, set the REVIEW/HIGH boundary to the lowest threshold achieving at least 90% observed precision on at least 20 labeled validation transactions. If no threshold qualifies, disable HIGH. The empirical target is not a confidence guarantee and excludes unknown outcomes.
4. Freeze both boundaries and report subsequent test volumes. Distribution shift and ties mean the 5% validation scenario is not a hard test-volume cap.

LOW means no automatic escalation by this model; it does not certify innocence. REVIEW means routine manual investigation. HIGH means prioritized human investigation; automatic blocking is not justified by this study. Known licit cases in these queues are a measurable proxy for unnecessary review and possible friction, not a count of actual customer harm. Transaction-level data cannot quantify unique customers or their costs.

`review_capacity.csv` separately evaluates an enforceable ranking policy: take the top ceil(fraction × bucket volume) per time step, breaking score ties by transaction ID, at 1%, 2%, 5%, 10%, and 20%. The labeled-only benchmark supplies conventional Precision@K and Recall@K. The all-traffic view charges unknown cases against analyst capacity and reports known illicit capture, known licit review, unknown volume, and lower/upper precision bounds. It cannot estimate population recall because unknown illicit cases have no ground truth.

Do not silently conflate these two policies. Fixed score bands provide consistent evidence thresholds but variable workload; per-bucket top-K enforces workload but changes the effective threshold as traffic changes. Real deployment requires analyst cost, loss severity, label maturation, calibrated scores, fairness checks, and prospective validation.
