import pandas as pd
from pandas.testing import assert_frame_equal
from fraudgraph.graph import snapshot_features


def fixture():
    nodes = pd.DataFrame({"txId": [1, 2, 3, 4], "Time step": [1, 1, 2, 1], "class": [1, 2, 3, 3]})
    edges = pd.DataFrame({"txId1": [1, 2], "txId2": [2, 3]})
    return nodes, edges


def test_future_nodes_and_edges_cannot_change_past():
    nodes, edges = fixture()
    actual, graph = snapshot_features(nodes, edges, 1)
    expected, _ = snapshot_features(nodes[nodes["Time step"] == 1], edges.iloc[:1], 1)
    assert_frame_equal(actual, expected)
    assert set(graph) == {1, 2, 4}
    assert set(graph.edges) == {(1, 2)}


def test_labels_have_no_effect():
    nodes, edges = fixture()
    before, _ = snapshot_features(nodes, edges, 2)
    nodes["class"] = [3, 1, 2, 1]
    after, _ = snapshot_features(nodes, edges, 2)
    assert_frame_equal(before, after)


def test_directed_degrees_component_and_isolate():
    nodes, edges = fixture()
    features, _ = snapshot_features(nodes, edges, 1)
    f = features.set_index("txId")
    assert f.loc[1, "g_in_degree"] == 0
    assert f.loc[1, "g_out_degree"] == 1
    assert f.loc[2, "g_component_size"] == 2
    assert f.loc[4, "g_component_size"] == 1
    assert f.loc[4, "g_neighbor_degree_mean"] == 0
    assert f.loc[4, "g_component_density"] == 0


def test_features_aligned_by_id_not_input_order():
    nodes, edges = fixture()
    a, _ = snapshot_features(nodes, edges, 1)
    b, _ = snapshot_features(nodes.iloc[::-1], edges, 1)
    assert_frame_equal(a.sort_values("txId").reset_index(drop=True), b.sort_values("txId").reset_index(drop=True), atol=1e-8)
