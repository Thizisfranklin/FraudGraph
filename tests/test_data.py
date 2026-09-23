import numpy as np
import pandas as pd
import pytest
from fraudgraph.data import LOCAL, load_validate


def write_fixture(root):
    raw = root / "data/raw"
    raw.mkdir(parents=True)
    f = pd.DataFrame({"txId": [11, 12, 13], "Time step": [1, 2, 3], **{c: [1., 2., 3.] for c in LOCAL}})
    f.to_csv(raw / "txs_features.csv", index=False)
    pd.DataFrame({"txId": [13, 11, 12], "class": [3, 1, 2]}).to_csv(raw / "txs_classes.csv", index=False)
    pd.DataFrame({"txId1": [11], "txId2": [12]}).to_csv(raw / "txs_edgelist.csv", index=False)
    return raw


def test_labels_join_by_id_and_unknown_stays_missing(tmp_path):
    write_fixture(tmp_path)
    f, _, _ = load_validate(tmp_path)
    assert f.set_index("txId").loc[11, "y"] == 1
    assert f.set_index("txId").loc[12, "y"] == 0
    assert np.isnan(f.set_index("txId").loc[13, "y"])


def test_duplicate_ids_rejected(tmp_path):
    raw = write_fixture(tmp_path)
    f = pd.read_csv(raw / "txs_features.csv")
    f.loc[1, "txId"] = 11
    f.to_csv(raw / "txs_features.csv", index=False)
    with pytest.raises(ValueError, match="duplicate transaction"):
        load_validate(tmp_path)


def test_dangling_edge_rejected(tmp_path):
    raw = write_fixture(tmp_path)
    pd.DataFrame({"txId1": [11], "txId2": [999]}).to_csv(raw / "txs_edgelist.csv", index=False)
    with pytest.raises(ValueError, match="dangling"):
        load_validate(tmp_path)


def test_embedded_target_disagreement_rejected(tmp_path):
    raw = write_fixture(tmp_path)
    f = pd.read_csv(raw / "txs_features.csv")
    f["class"] = 3
    f.to_csv(raw / "txs_features.csv", index=False)
    with pytest.raises(ValueError, match="Embedded labels"):
        load_validate(tmp_path)
