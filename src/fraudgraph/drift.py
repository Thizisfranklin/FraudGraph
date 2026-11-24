"""Exploratory feature, prediction, and known-label drift diagnostics.

These are retrospective diagnostics, not a verified drift *cause* detector.
Unknown outcomes remain missing. Baseline bins are fit using historical data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from sklearn.metrics import average_precision_score


def population_stability_index(reference, current, bins=10, epsilon=1e-6):
    """PSI with *reference-derived* quantile bin edges and explicit missing bins.

    A constant reference feature can still drift: nonmatching later values
    land outside its observed reference support.
    """
    a = np.asarray(reference, dtype=float)
    b = np.asarray(current, dtype=float)
    if not len(a) or not len(b):
        return float("nan")
    af, bf = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(af):
        return float("nan")
    edges = np.unique(np.quantile(af, np.linspace(0, 1, bins + 1)))
    # Infinite endpoints retain out-of-range observations.
    boundaries = np.r_[-np.inf, edges[1:-1], np.inf]
    ac = np.histogram(af, bins=boundaries)[0].astype(float)
    bc = np.histogram(bf, bins=boundaries)[0].astype(float)
    ac = np.r_[ac, len(a) - len(af)]
    bc = np.r_[bc, len(b) - len(bf)]
    pa = np.maximum(ac / len(a), epsilon)
    pb = np.maximum(bc / len(b), epsilon)
    return float(np.sum((pb - pa) * np.log(pb / pa)))


def feature_shift(reference, current, columns, period):
    """One row per feature and period; no outcomes used."""
    rows = []
    for col in columns:
        a = pd.to_numeric(reference[col], errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(current[col], errors="coerce").to_numpy(dtype=float)
        af, bf = a[np.isfinite(a)], b[np.isfinite(b)]
        rows.append({
            "time_step": int(period), "feature": col,
            "reference_n": len(a), "current_n": len(b),
            "reference_missing_rate": float(np.mean(~np.isfinite(a))),
            "current_missing_rate": float(np.mean(~np.isfinite(b))),
            "reference_median": float(np.median(af)) if len(af) else np.nan,
            "current_median": float(np.median(bf)) if len(bf) else np.nan,
            "psi": population_stability_index(a, b),
            "wasserstein": float(wasserstein_distance(af, bf)) if len(af) and len(bf) else np.nan,
        })
    return rows


def score_and_label_summary(frame, score_column=None):
    """Known-label AP and prevalence, plus unknown coverage and score drift.

    AP is undefined when only one known class is present. Do not replace it
    with a misleading zero or use unknowns as negatives.
    """
    rows = []
    for period, part in frame.groupby("Time step", sort=True):
        known = part.loc[part.y.notna()]
        n_pos = int((known.y == 1).sum())
        n_neg = int((known.y == 0).sum())
        prevalence = float(n_pos / len(known)) if len(known) else np.nan
        row = {
            "time_step": int(period), "transactions": len(part),
            "labeled": len(known), "known_illicit": n_pos, "known_licit": n_neg,
            "unknown": len(part) - len(known),
            "known_label_coverage": float(len(known) / len(part)),
            "known_illicit_prevalence": prevalence,
        }
        if score_column and score_column in part:
            score = pd.to_numeric(part[score_column], errors="coerce")
            row["score_median_all"] = float(score.median()) if score.notna().any() else np.nan
            row["score_p95_all"] = float(score.quantile(.95)) if score.notna().any() else np.nan
            valid = known[known[score_column].notna()]
            if valid.y.nunique() == 2:
                ap = float(average_precision_score(valid.y.astype(int), valid[score_column]))
                row["average_precision_labeled"] = ap
                row["ap_above_prevalence"] = ap - float(valid.y.mean())
            else:
                row["average_precision_labeled"] = np.nan
                row["ap_above_prevalence"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def ranked_shift(frame, reference, columns, periods):
    """Compute feature-shift tables using one historical reference cohort."""
    rows = []
    for period in periods:
        current = frame.loc[frame["Time step"] == period]
        if len(current):
            rows.extend(feature_shift(reference, current, columns, period))
    return pd.DataFrame(rows)
