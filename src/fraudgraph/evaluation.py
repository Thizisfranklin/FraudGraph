"""Validation-only policy selection and honest capacity evaluation."""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve


def metrics(y, score, threshold):
    y = np.asarray(y, dtype=int)
    score = np.asarray(score)
    tn, fp, fn, tp = confusion_matrix(y, score >= threshold, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / (tp + fn) if tp + fn else 0.
    return {"pr_auc_ap": float(average_precision_score(y, score)), "precision": float(precision),
            "recall": float(recall), "f1": float(2 * precision * recall / (precision + recall)) if precision + recall else 0.,
            "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.,
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def f1_threshold(y, score):
    p, r, thresholds = precision_recall_curve(y, score)
    f = np.divide(2 * p[:-1] * r[:-1], p[:-1] + r[:-1], out=np.zeros_like(p[:-1]), where=(p[:-1] + r[:-1]) > 0)
    return float(thresholds[np.argmax(f)])


def policy_thresholds(y, score, all_scores, review_fraction, target, min_cases):
    """Low boundary from all validation traffic; high boundary from labeled evidence."""
    low = float(np.quantile(all_scores, 1 - review_fraction, method="higher"))
    y, score = np.asarray(y), np.asarray(score)
    # Operate at unique thresholds, so ties cannot manufacture precision.
    candidates = []
    for t in np.unique(score[score >= low]):
        selected = score >= t
        n = selected.sum()
        if n >= min_cases and y[selected].mean() >= target:
            candidates.append(float(t))
    high = min(candidates) if candidates else float("inf")
    return low, high


def capacity_table(frame, score_col, fractions=(.01, .02, .05, .1, .2)):
    """Rank each time bucket. Unknowns consume capacity, not known negatives."""
    rows = []
    for scope in ["labeled_only", "all_transactions"]:
        pool = frame[frame.y.notna()] if scope == "labeled_only" else frame
        for fraction in fractions:
            selections = []
            for _, bucket in pool.groupby("Time step"):
                k = max(1, int(np.ceil(len(bucket) * fraction)))
                selections.append(bucket.sort_values([score_col, "txId"], ascending=[False, True]).head(k))
            selected = pd.concat(selections)
            tp = int((selected.y == 1).sum())
            fp = int((selected.y == 0).sum())
            unknown = int(selected.y.isna().sum())
            total_positive = int((pool.y == 1).sum())
            rows.append({"scope": scope, "capacity_fraction": fraction, "reviewed": len(selected),
                         "known_illicit": tp, "known_licit": fp, "unknown": unknown,
                         "precision_at_k_known": tp / (tp + fp) if tp + fp else np.nan,
                         "recall_at_k_known": tp / total_positive if total_positive else np.nan,
                         "precision_lower_bound_all": tp / len(selected),
                         "precision_upper_bound_all": (tp + unknown) / len(selected)})
    return pd.DataFrame(rows)


def paired_time_bootstrap(frame, baseline, enhanced, repetitions=1000, seed=42):
    """Resample entire time buckets, preserving paired predictions and within-bucket dependence."""
    known = frame[frame.y.notna()]
    groups = [g for _, g in known.groupby("Time step")]
    rng = np.random.default_rng(seed)
    delta = []
    for _ in range(repetitions):
        sample = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if sample.y.nunique() == 2:
            delta.append(average_precision_score(sample.y, sample[enhanced]) - average_precision_score(sample.y, sample[baseline]))
    return {"delta_ap": float(average_precision_score(known.y, known[enhanced]) - average_precision_score(known.y, known[baseline])),
            "ci_95_low": float(np.quantile(delta, .025)), "ci_95_high": float(np.quantile(delta, .975)),
            "repetitions": repetitions, "valid_repetitions": len(delta), "unit": "time bucket", "seed": seed}
