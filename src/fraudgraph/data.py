"""Source acquisition and strict validation; unknown is never a negative label."""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd

SOURCE = "https://github.com/git-disl/EllipticPlusPlus.git"
REVISION = "08fe6aded83afb97bf5a79a71130f542ca783c2e"
FILES = ("txs_features.csv", "txs_classes.csv", "txs_edgelist.csv")
LOCAL = ["total_BTC", "fees", "size", "num_input_addresses", "num_output_addresses",
         "in_BTC_min", "in_BTC_max", "in_BTC_mean", "in_BTC_median", "in_BTC_total",
         "out_BTC_min", "out_BTC_max", "out_BTC_mean", "out_BTC_median", "out_BTC_total"]


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire(root):
    """Download only the transaction files from pinned Git LFS objects."""
    import requests
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        path = raw / name
        pointer_url = f"https://raw.githubusercontent.com/git-disl/EllipticPlusPlus/{REVISION}/Transactions%20Dataset/{name}"
        r = requests.get(pointer_url, timeout=60)
        r.raise_for_status()
        pointer = r.text
        if not pointer.startswith("version https://git-lfs.github.com/spec/v1"):
            raise ValueError("Expected a Git LFS pointer from the pinned source")
        expected_hash = pointer.split("oid sha256:")[1].splitlines()[0]
        expected_size = int(pointer.split("size ")[1].splitlines()[0])
        if path.exists() and path.stat().st_size == expected_size and digest(path) == expected_hash:
            print(f"Verified cached {name}", flush=True)
            continue
        url = f"https://media.githubusercontent.com/media/git-disl/EllipticPlusPlus/{REVISION}/Transactions%20Dataset/{name}"
        temporary = path.with_suffix(".partial")
        with requests.get(url, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with temporary.open("wb") as f:
                for chunk in response.iter_content(1024 * 1024):
                    f.write(chunk)
        if temporary.stat().st_size != expected_size or digest(temporary) != expected_hash:
            raise ValueError(f"Checksum mismatch: {name}")
        temporary.replace(path)
        print(f"Downloaded and verified {name}", flush=True)


def load_validate(root):
    raw = root / "data/raw"
    f = pd.read_csv(raw / FILES[0])
    labels = pd.read_csv(raw / FILES[1])
    edges = pd.read_csv(raw / FILES[2])
    if not {"txId", "Time step", *LOCAL}.issubset(f):
        raise ValueError("Missing required feature columns")
    if list(labels.columns) != ["txId", "class"] or list(edges.columns) != ["txId1", "txId2"]:
        raise ValueError("Unexpected label/edge schema")
    for name, frame in [("features", f), ("labels", labels)]:
        if frame.txId.isna().any() or frame.txId.duplicated().any():
            raise ValueError(f"Missing or duplicate transaction IDs in {name}")
    if set(labels.txId) != set(f.txId):
        raise ValueError("Feature/label transaction sets differ")
    if not labels["class"].isin([1, 2, 3]).all():
        raise ValueError("Unexpected label; require illicit=1, licit=2, unknown=3")
    if "class" in f:
        aligned = labels.set_index("txId")["class"].reindex(f.txId).to_numpy()
        if not np.array_equal(f["class"], aligned):
            raise ValueError("Embedded labels disagree with label file")
        f = f.drop(columns="class")
    if f["Time step"].isna().any() or not f["Time step"].between(1, 49).all():
        raise ValueError("Invalid time steps")
    if not np.equal(f["Time step"], f["Time step"].astype(int)).all():
        raise ValueError("Non-integer time steps")
    if edges.isna().any().any() or not edges.isin(set(f.txId)).all().all():
        raise ValueError("Missing/dangling edge endpoints")
    duplicate_edges = int(edges.duplicated().sum())
    self_loops = int((edges.txId1 == edges.txId2).sum())
    edges = edges.drop_duplicates().reset_index(drop=True)
    if self_loops:
        raise ValueError("Unexpected self-loop")
    numeric = f.drop(columns="txId")
    if np.isinf(numeric.to_numpy()).any():
        raise ValueError("Infinite feature values")
    times = f.set_index("txId")["Time step"]
    source_t, target_t = edges.txId1.map(times), edges.txId2.map(times)
    f = f.merge(labels, on="txId", validate="one_to_one")
    f = pd.concat([f, f["class"].map({1: 1, 2: 0}).rename("y")], axis=1)
    stats = {
        "nodes": len(f), "raw_edges": len(edges) + duplicate_edges, "unique_edges": len(edges),
        "duplicate_ids": 0, "duplicate_edges": duplicate_edges, "self_loops": self_loops,
        "missing_feature_cells": int(numeric.isna().sum().sum()),
        "missing_by_column": numeric.isna().sum().loc[lambda s: s > 0].to_dict(),
        "class_counts": f["class"].value_counts().sort_index().to_dict(),
        "timesteps": sorted(f["Time step"].unique().tolist()),
        "same_step_edges": int((source_t == target_t).sum()),
        "forward_step_edges": int((source_t < target_t).sum()),
        "backward_step_edges": int((source_t > target_t).sum()),
        "duplicate_local_feature_rows": int(f[LOCAL].duplicated().sum()),
        "source_repository": SOURCE, "source_commit": REVISION,
        "files": {name: {"sha256": digest(raw / name), "bytes": (raw / name).stat().st_size} for name in FILES},
    }
    return f, edges, stats
