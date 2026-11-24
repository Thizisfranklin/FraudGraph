"""Temporal robustness checks: capacity, overfit diagnostics, and label-lag scenarios.

Exploratory research only. Model configuration is selected on earlier validation
periods. Test periods 40-49 have already been inspected and are not a pristine
holdout. These scores are NOT calibrated probabilities of wrongdoing.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier

from .adaptation import eligible_training


@dataclass(frozen=True)
class CapacityPreset:
    name: str
    max_depth: int
    n_estimators: int
    min_child_weight: int
    reg_lambda: float
    reg_alpha: float
    subsample: float
    colsample_bytree: float
    learning_rate: float = 0.05


# Prespecified capacity / regularization contrast, including simple and complex
# models to detect possible UNDERfitting as well as OVERfitting.
CAPACITY_PRESETS = (
    CapacityPreset("low_capacity", 2, 90, 12, 12., 1., .8, .8),
    CapacityPreset("regularized", 3, 150, 10, 12., .5, .8, .8),
    CapacityPreset("reference_capacity", 3, 150, 5, 5., 0., .9, .9),
    CapacityPreset("high_capacity", 5, 280, 2, 2., 0., .95, .95),
)
STRATEGIES = ("frozen", "expanding", "rolling", "recency")


def make_regularized_model(preset, seed=42, threads=2):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        XGBClassifier(
            objective="binary:logistic", eval_metric="aucpr",
            max_depth=preset.max_depth, n_estimators=preset.n_estimators,
            min_child_weight=preset.min_child_weight,
            reg_lambda=preset.reg_lambda, reg_alpha=preset.reg_alpha,
            subsample=preset.subsample, colsample_bytree=preset.colsample_bytree,
            learning_rate=preset.learning_rate, tree_method="hist",
            random_state=seed, n_jobs=threads,
        ),
    )


def known_average_precision(y, score):
    """AP is undefined if a period has only one observed class."""
    y, score = np.asarray(y), np.asarray(score, dtype=float)
    valid = np.isfinite(y) & np.isfinite(score)
    if len(np.unique(y[valid])) < 2:
        return float("nan")
    return float(average_precision_score(y[valid].astype(int), score[valid]))


def analyst_capacity(bucket, score, fractions=(.01, .05, .10)):
    """Top-K on ALL transactions; unknown cases consume review capacity.

    Known illicit capture is recall among known illicit cases only.
    Bounds on precision assume all unknown cases could be licit or illicit.
    """
    if not {"txId", "y"}.issubset(bucket.columns):
        raise ValueError("bucket needs txId and y")
    if bucket.txId.duplicated().any():
        raise ValueError("duplicate transaction IDs")
    scores = np.asarray(score, dtype=float)
    if len(scores) != len(bucket) or not np.isfinite(scores).all():
        raise ValueError("finite scores must align with the bucket")
    if not set(bucket.y.dropna().unique()).issubset({0., 1.}):
        raise ValueError("unknown outcomes must be represented as NaN")
    ranked = bucket[["txId", "y"]].copy().assign(score=scores)
    ranked = ranked.sort_values(["score", "txId"], ascending=[False, True])
    positives = int((bucket.y == 1).sum())
    rows = []
    for frac in fractions:
        if not 0 < frac <= 1:
            raise ValueError("capacity fraction must be in (0, 1]")
        selected = ranked.head(max(1, int(np.ceil(len(ranked) * frac))))
        illicit = int((selected.y == 1).sum())
        licit = int((selected.y == 0).sum())
        unknown = int(selected.y.isna().sum())
        rows.append({
            "capacity_fraction": frac, "reviewed": len(selected),
            "known_illicit": illicit, "known_licit": licit, "unknown": unknown,
            "known_illicit_capture": illicit / positives if positives else np.nan,
            "precision_lower_bound": illicit / len(selected),
            "precision_upper_bound": (illicit + unknown) / len(selected),
        })
    return rows


def one_forward_fold(frame, features, target_step, strategy, preset,
                     label_lag, seed=42, threads=2):
    """Train only on labels hypothetically mature before target_step."""
    training, weights, last_label_step = eligible_training(
        frame, target_step, strategy, label_lag=label_lag
    )
    target = frame.loc[frame["Time step"] == target_step]
    if target.empty:
        raise ValueError(f"No transactions at step {target_step}")
    model = make_regularized_model(preset, seed, threads)
    model.fit(training[features], training.y.astype(int),
              xgbclassifier__sample_weight=weights)
    train_score = model.predict_proba(training[features])[:, 1]
    target_score = model.predict_proba(target[features])[:, 1]
    known = target.y.notna().to_numpy()
    target_labeled = target.loc[known]
    train_ap = known_average_precision(training.y, train_score)
    target_ap = known_average_precision(target_labeled.y, target_score[known])
    train_prevalence = float(training.y.mean())
    target_prevalence = float(target_labeled.y.mean()) if len(target_labeled) else np.nan
    row = {
        "time_step": int(target_step), "strategy": strategy,
        "capacity_preset": preset.name,
        "candidate": f"{strategy}__{preset.name}",
        "label_lag": int(label_lag),
        "last_labeled_training_step": int(last_label_step),
        "trained_labeled": len(training),
        "evaluated_labeled": len(target_labeled),
        "known_illicit": int((target_labeled.y == 1).sum()),
        "train_prevalence": train_prevalence,
        "target_prevalence": target_prevalence,
        "train_ap_in_sample": train_ap,
        "forward_ap": target_ap,
        "train_ap_above_prevalence": train_ap - train_prevalence,
        "forward_ap_above_prevalence": target_ap - target_prevalence
        if np.isfinite(target_ap) else np.nan,
        "excess_ap_gap": (train_ap - train_prevalence) -
                         (target_ap - target_prevalence)
                         if np.isfinite(target_ap) else np.nan,
    }
    capacity = analyst_capacity(target, target_score)
    for record in capacity:
        record.update({
            "time_step": int(target_step), "candidate": row["candidate"],
            "label_lag": int(label_lag), "strategy": strategy,
            "capacity_preset": preset.name,
        })
    return row, capacity


def choose_by_validation(folds):
    """Choose one model *per label-lag scenario* using validation folds only.

    Optimize worst-period AP primarily, then mean AP, then lower model capacity.
    This is a declared experimental criterion, not necessarily the best business
    objective. Never treat label lag itself as a tunable performance parameter.
    """
    rows = []
    for (lag, candidate), group in folds.groupby(["label_lag", "candidate"]):
        if group.forward_ap.isna().any():
            continue
        rows.append({
            "label_lag": int(lag), "candidate": candidate,
            "strategy": group.strategy.iloc[0],
            "capacity_preset": group.capacity_preset.iloc[0],
            "folds": len(group),
            "mean_forward_ap": float(group.forward_ap.mean()),
            "worst_forward_ap": float(group.forward_ap.min()),
            "mean_ap_lift": float(group.forward_ap_above_prevalence.mean()),
            "mean_excess_ap_gap": float(group.excess_ap_gap.mean()),
        })
    summary = pd.DataFrame(rows)
    if summary.empty:
        raise ValueError("No valid candidates: every fold needs both known classes")
    # Conservative comparison: penalize the lowest-ranked validation period.
    complexity = {p.name: i for i, p in enumerate(CAPACITY_PRESETS)}
    summary["complexity_order"] = summary.capacity_preset.map(complexity)
    summary = summary.sort_values(
        ["label_lag", "worst_forward_ap", "mean_forward_ap",
         "complexity_order", "candidate"],
        ascending=[True, False, False, True, True],
    ).reset_index(drop=True)
    selected = summary.groupby("label_lag", sort=True).head(1).copy()
    return summary, selected


def validation_backtest(frame, features, label_lags=(2, 4, 6),
                        steps=(35, 37, 39), seed=42, threads=2):
    """Fixed folds, preset model capacities, and prespecified label delays."""
    if min(steps) - max(label_lags) < 29:
        raise ValueError("All validation steps must follow frozen training and label lag")
    fold_rows, capacity_rows = [], []
    for lag in label_lags:
        for strategy in STRATEGIES:
            for preset in CAPACITY_PRESETS:
                for step in steps:
                    fold, capacity = one_forward_fold(
                        frame, features, step, strategy, preset, lag, seed, threads
                    )
                    fold_rows.append(fold)
                    capacity_rows.extend(capacity)
    folds = pd.DataFrame(fold_rows)
    summary, selected = choose_by_validation(folds)
    return folds, pd.DataFrame(capacity_rows), summary, selected


def replay_selected(frame, features, selected, steps=range(40, 50),
                    seed=42, threads=2):
    """Explicitly post-hoc: test steps were inspected before study design."""
    fold_rows, capacity_rows = [], []
    for row in selected.itertuples(index=False):
        preset = next(p for p in CAPACITY_PRESETS if p.name == row.capacity_preset)
        for step in steps:
            fold, capacity = one_forward_fold(
                frame, features, step, row.strategy, preset,
                int(row.label_lag), seed, threads
            )
            fold_rows.append(fold)
            capacity_rows.extend(capacity)
    return pd.DataFrame(fold_rows), pd.DataFrame(capacity_rows)
