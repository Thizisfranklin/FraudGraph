"""Verify saved claims against predictions, execution outputs, and source hashes."""
from pathlib import Path
import json
import hashlib
import nbformat
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from fraudgraph.data import digest

root = Path(__file__).resolve().parents[1]
reports = root / "reports"
manifest = json.loads((reports / "run_manifest.json").read_text())
assert manifest["results_sha256"] == digest(reports / "results.csv")
for name, expected in manifest["source_code_sha256"].items():
    assert digest(root / "src/fraudgraph" / name) == expected, f"Unexecuted source change: {name}"
predictions = pd.read_parquet(reports / "predictions.parquet")
known = predictions[predictions.y.notna()]
results = pd.read_csv(reports / "results.csv")
assert len(results) == 16
for row in results[results.split == "test"].itertuples():
    assert np.isclose(row.pr_auc_ap, average_precision_score(known.y, known[row.experiment_id]), atol=1e-12)
    assert row.tp + row.fn == int(known.y.sum())
    assert row.tp + row.fn + row.tn + row.fp == len(known)
executions = []
for path in sorted((root / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert cells and all(cell.execution_count is not None for cell in cells), path.name
    assert all(output.output_type != "error" for cell in cells for output in cell.outputs), path.name
    executions.append({"notebook": path.name, "executed_code_cells": len(cells), "sha256": digest(path)})
assert len(executions) == 7
ledger = [json.loads(line) for line in (reports / "experiment_log.jsonl").read_text().splitlines()]
for name in results.experiment_id.unique():
    attempts = [row["pr_auc_ap"] for row in ledger if row["experiment_id"] == name and row["split"] == "test"]
    assert np.allclose(attempts, attempts[-1], atol=1e-12), name
summary = {"evidence_run": manifest["run_id"], "saved_ap_matches_predictions": True,
           "source_hashes_match_executed_run": True, "repeated_main_metrics_match": True,
           "notebooks": executions, "main_ledger_records": len(ledger)}
(reports / "artifact_verification.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
