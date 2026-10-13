"""Read-only, audited access to FraudGraph's committed evaluation outputs.

The explorer never retrains a model, infers missing labels, or recalculates
transaction risk scores. All displayed outcomes come from saved reports.
"""
from pathlib import Path

import pandas as pd


SCHEMAS = {
    "results": {"experiment_id", "split", "pr_auc_ap"},
    "review_capacity": {
        "scope", "capacity_fraction", "reviewed", "known_illicit",
        "known_licit", "unknown", "experiment_id", "split",
    },
    "test_by_time": {"experiment_id", "time_step", "labeled", "illicit", "ap"},
    "cases": {
        "case", "txId", "time_step", "class", "score",
        "baseline_score", "neighbors_total", "neighbors_shown",
    },
}


def load_reports(reports_dir: Path) -> dict[str, pd.DataFrame]:
    """Load only small, committed summary artifacts (never raw blockchain data)."""
    reports_dir = Path(reports_dir)
    tables = {}
    for name, columns in SCHEMAS.items():
        path = reports_dir / f"{name}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing committed report: {path}")
        table = pd.read_csv(path)
        missing = columns - set(table.columns)
        if missing:
            raise ValueError(f"{path.name} is missing fields: {sorted(missing)}")
        tables[name] = table
    return tables


def exact_row(table: pd.DataFrame, **filters) -> pd.Series:
    selected = table
    for column, value in filters.items():
        selected = selected.loc[selected[column] == value]
    if len(selected) != 1:
        raise ValueError(f"Expected one report row for {filters}; found {len(selected)}")
    return selected.iloc[0]


def test_ap(results: pd.DataFrame, experiment_id: str) -> float:
    return float(exact_row(
        results, experiment_id=experiment_id, split="test"
    )["pr_auc_ap"])


def test_curve(capacity: pd.DataFrame, experiment_id: str) -> pd.DataFrame:
    rows = capacity.loc[
        (capacity["experiment_id"] == experiment_id)
        & (capacity["split"] == "test")
        & (capacity["scope"] == "all_transactions")
    ].sort_values("capacity_fraction").copy()
    if rows.empty:
        raise ValueError(f"No all-transaction test-capacity rows: {experiment_id}")
    return rows


def known_illicit_total(by_time: pd.DataFrame, experiment_id: str) -> int:
    rows = by_time.loc[by_time["experiment_id"] == experiment_id]
    if rows.empty or rows["time_step"].duplicated().any():
        raise ValueError(f"Invalid time-step rows: {experiment_id}")
    return int(rows["illicit"].sum())


def capacity_at(
    capacity: pd.DataFrame, by_time: pd.DataFrame,
    experiment_id: str, fraction: float,
) -> dict:
    row = exact_row(
        capacity, experiment_id=experiment_id, split="test",
        scope="all_transactions", capacity_fraction=fraction,
    )
    reviewed = int(row["reviewed"])
    found = int(row["known_illicit"])
    licit = int(row["known_licit"])
    unknown = int(row["unknown"])
    if reviewed != found + licit + unknown:
        raise ValueError("Review capacity report does not reconcile")
    total_known_illicit = known_illicit_total(by_time, experiment_id)
    return {
        "reviewed": reviewed,
        "known_illicit": found,
        "known_licit": licit,
        "unknown": unknown,
        "total_known_illicit": total_known_illicit,
        "known_illicit_recall": found / total_known_illicit,
    }


def comparison_ids(family: str, learner: str) -> tuple[str, str]:
    if family not in ("named", "extended") or learner not in ("xgboost", "logistic"):
        raise ValueError("Unknown pre-registered experiment family/learner")
    stem = f"{family}_{learner}"
    return f"{stem}_tx", f"{stem}_graph"
