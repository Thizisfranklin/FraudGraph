"""Graph features at the end of each observed time bucket; no label inputs."""
import networkx as nx
import numpy as np
import pandas as pd

GRAPH_FEATURES = ["g_in_degree", "g_out_degree", "g_total_degree", "g_pagerank_scaled",
                  "g_component_size", "g_component_density", "g_neighbor_degree_mean",
                  "g_reciprocal_fraction"]


def snapshot_features(nodes, edges, cutoff):
    """Only nodes with time <= cutoff and edges between those nodes can enter."""
    visible = nodes.loc[nodes["Time step"] <= cutoff, "txId"].tolist()
    visible_set = set(visible)
    e = edges[edges.txId1.isin(visible_set) & edges.txId2.isin(visible_set)]
    g = nx.DiGraph()
    g.add_nodes_from(visible)
    g.add_edges_from(e.itertuples(index=False, name=None))
    if not visible:
        return pd.DataFrame(columns=["txId", *GRAPH_FEATURES]), g
    rank = nx.pagerank(g, alpha=0.85, tol=1e-10, max_iter=300)
    component = {}
    for members in nx.weakly_connected_components(g):
        n = len(members)
        m = sum(g.out_degree(v) for v in members)
        density = m / (n * (n - 1)) if n > 1 else 0.0
        for v in members:
            component[v] = (n, density)
    rows = []
    for v in nodes.loc[nodes["Time step"] == cutoff, "txId"]:
        neighbors = set(g.predecessors(v)) | set(g.successors(v))
        reciprocal = len(set(g.predecessors(v)) & set(g.successors(v)))
        rows.append([v, g.in_degree(v), g.out_degree(v), g.degree(v), rank[v] * len(g),
                     *component[v], np.mean([g.degree(w) for w in neighbors]) if neighbors else 0.,
                     reciprocal / len(neighbors) if neighbors else 0.])
    return pd.DataFrame(rows, columns=["txId", *GRAPH_FEATURES]), g


def build_features(nodes, edges):
    frames = []
    for t in sorted(nodes["Time step"].unique()):
        frame, graph = snapshot_features(nodes[["txId", "Time step"]], edges, t)
        frames.append(frame)
        if t % 10 == 0:
            print(f"Graph snapshots through step {t}", flush=True)
    result = pd.concat(frames, ignore_index=True)
    if result.txId.duplicated().any() or set(result.txId) != set(nodes.txId):
        raise ValueError("Graph features did not align one-to-one")
    if not np.isfinite(result[GRAPH_FEATURES].to_numpy()).all():
        raise ValueError("Nonfinite graph feature")
    components = [len(c) for c in nx.weakly_connected_components(graph)]
    stats = {"nodes": len(graph), "edges": graph.number_of_edges(), "directed": graph.is_directed(),
             "isolated": nx.number_of_isolates(graph), "weak_components": len(components),
             "largest_component": max(components),
             "strong_components": nx.number_strongly_connected_components(graph),
             "degree_quantiles": dict(zip(["min", "median", "p95", "p99", "max"],
                 np.quantile([d for _, d in graph.degree()], [0, .5, .95, .99, 1]).tolist()))}
    return result, graph, stats
