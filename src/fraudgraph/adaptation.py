"""Chronological experiments for temporal robustness (explicitly post-hoc).

Validation selects strategy and XGBoost settings. Test evaluation is a
retrospective *forward replay*: newly available labels may enter training
only after the declared label lag. Observed test drift informed this project,
so the replay is NOT a pristine future holdout result.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier


@dataclass(frozen=True)
class Specification:
    strategy: str
    max_depth: int = 4
    n_estimators: int = 250
    learning_rate: float = 0.05
    rolling_steps: int = 15
    half_life_steps: float = 8.

    @property
    def name(self):
        return f"{self.strategy}_depth{self.max_depth}_trees{self.n_estimators}_lr{self.learning_rate:g}"


def eligible_training(frame, target_step, strategy, label_lag=2,
                      fixed_train_end=29, rolling_steps=15, half_life_steps=8.):
    """Return labeled history and weights without access to future outcomes.

    At target_step T, labels through T - label_lag are *assumed* available;
    this must be verified with real label-maturation timestamps in deployment.
    A frozen model uses historical training through fixed_train_end only.
    """
    if label_lag < 1:
        raise ValueError("label_lag must be >= 1")
    last_available = int(target_step) - int(label_lag)
    if strategy == "frozen":
        if fixed_train_end > last_available:
            raise ValueError("Frozen training would use labels unavailable at target time")
        end = fixed_train_end
    elif strategy in {"expanding", "rolling", "recency"}:
        end = last_available
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    selected = (frame["Time step"] <= end) & frame.y.notna()
    if strategy == "rolling":
        selected &= frame["Time step"] > end - rolling_steps
    train = frame.loc[selected]
    if train.empty or train.y.nunique() < 2:
        raise ValueError(f"Not enough labeled training examples for step {target_step}")
    if strategy == "recency":
        weights = np.exp(-np.log(2) * (end - train["Time step"].to_numpy()) / half_life_steps)
    else:
        weights = np.ones(len(train), dtype=float)
    return train, weights, end


def xgboost_pipeline(spec, seed=42, threads=2):
    """The historical baseline settings plus a small temporal search space."""
    return make_pipeline(
        SimpleImputer(strategy="median"),
        XGBClassifier(
            n_estimators=spec.n_estimators, max_depth=spec.max_depth,
            learning_rate=spec.learning_rate, subsample=.9, colsample_bytree=.9,
            min_child_weight=5, reg_lambda=5, tree_method="hist",
            eval_metric="aucpr", random_state=seed, n_jobs=threads,
        )
    )


def evaluate_target(frame, target_step, cols, spec, label_lag=2, seed=42, threads=2):
    """One honest-by-construction forward fold, conditional on label maturity."""
    train, weights, cutoff = eligible_training(
        frame, target_step, spec.strategy, label_lag=label_lag,
        rolling_steps=spec.rolling_steps, half_life_steps=spec.half_life_steps
    )
    target = frame.loc[frame["Time step"] == target_step]
    if target.empty:
        raise ValueError(f"Missing target bucket {target_step}")
    model = xgboost_pipeline(spec, seed=seed, threads=threads)
    model.fit(train[cols], train.y.astype(int),
              xgbclassifier__sample_weight=weights)
    score = model.predict_proba(target[cols])[:, 1]
    known = target.y.notna().to_numpy()
    known_y = target.loc[known, "y"].astype(int)
    ap = (float(average_precision_score(known_y, score[known]))
          if known_y.nunique() == 2 else np.nan)
    prevalence = float(known_y.mean()) if len(known_y) else np.nan
    return {
        "spec": spec.name, "strategy": spec.strategy,
        "time_step": int(target_step), "last_training_step": int(cutoff),
        "label_lag_assumed": int(label_lag), "trained_labeled": len(train),
        "evaluated_labeled": len(known_y), "known_illicit": int(known_y.sum()),
        "total_traffic": len(target),
        "prevalence": prevalence, "ap": ap,
        "ap_above_prevalence": ap - prevalence if np.isfinite(ap) else np.nan,
    }


def temporal_validation_search(frame, cols, validation_steps=(31, 33, 35, 37, 39),
                               label_lag=2, seed=42, threads=2):
    """Select one candidate using validation folds only, never test outcomes."""
    options = [
        Specification(strategy, max_depth=depth, n_estimators=trees, learning_rate=lr)
        for strategy in ("frozen", "expanding", "rolling", "recency")
        for depth, trees, lr in ((3, 150, .05), (4, 250, .05), (5, 250, .03))
    ]
    rows = []
    for spec in options:
        for step in validation_steps:
            rows.append(evaluate_target(frame, step, cols, spec, label_lag, seed, threads))
    validation = pd.DataFrame(rows)
    summary = validation.groupby(["spec", "strategy"], as_index=False).agg(
        mean_validation_ap=("ap", "mean"),
        worst_validation_ap=("ap", "min"),
        mean_ap_above_prevalence=("ap_above_prevalence", "mean"),
        folds=("ap", "count"),
    )
    summary = summary.sort_values(
        ["mean_validation_ap", "worst_validation_ap", "spec"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    selected = next(x for x in options if x.name == summary.iloc[0]["spec"])
    return selected, validation, summary


def evaluate_selected_on_future(frame, cols, selected, steps=range(40, 50),
                                label_lag=2, seed=42, threads=2):
    """Test is retrospective, since drift at these steps was already inspected."""
    return pd.DataFrame([
        evaluate_target(frame, step, cols, selected, label_lag, seed, threads)
        for step in steps
    ])


def feature_ablation_experiments(frame, named_cols, graph_cols, seed=42, threads=2):
    """Exploratory, fixed-history feature ablations; never tune with test results."""
    candidates = {
        "transaction_only": list(named_cols),
        "degree_only": list(named_cols) + [x for x in graph_cols if x in {
            "g_in_degree", "g_out_degree", "g_total_degree"}],
        "without_component": list(named_cols) + [x for x in graph_cols
                                                   if not x.startswith("g_component_")
                                                   and x != "g_reciprocal_fraction"],
        "all_graph_nonconstant": list(named_cols) + [x for x in graph_cols
                                                      if x != "g_reciprocal_fraction"],
        "without_transaction_size": [x for x in named_cols if x != "size"] +
                                    [x for x in graph_cols if x != "g_reciprocal_fraction"],
    }
    rows = []
    spec = Specification("frozen")
    train = frame[(frame["Time step"] <= 29) & frame.y.notna()]
    for name, cols in candidates.items():
        model = xgboost_pipeline(spec, seed=seed, threads=threads)
        model.fit(train[cols], train.y.astype(int))
        for bucket, part in frame.loc[frame["Time step"].between(30, 49)].groupby("Time step"):
            known = part.y.notna().to_numpy()
            y = part.loc[known, "y"].astype(int)
            scores = model.predict_proba(part[cols])[:, 1]
            ap = float(average_precision_score(y, scores[known])) if y.nunique() == 2 else np.nan
            prevalence = float(y.mean()) if len(y) else np.nan
            rows.append({"feature_group": name, "time_step": int(bucket),
                         "period": "validation" if bucket <= 39 else "posthoc_test",
                         "n_features": len(cols), "known_illicit": int(y.sum()),
                         "known_labeled": len(y), "prevalence": prevalence, "ap": ap,
                         "ap_above_prevalence": ap - prevalence if np.isfinite(ap) else np.nan})
    return pd.DataFrame(rows)
