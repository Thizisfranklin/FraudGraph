"""Small, purposeful figures; network cases are selected by a recorded rule."""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fraudgraph-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve
import plotly.graph_objects as go

COLORS = {1: "#c84b31", 2: "#227c9d", 3: "#b6bcc5"}


def save(fig, root, name):
    fig.tight_layout()
    fig.savefig(root / "reports/figures" / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def eda(root, frame, graph, config):
    by_time = pd.crosstab(frame["Time step"], frame["class"]).rename(columns={1:"Illicit", 2:"Licit", 3:"Unknown"})
    by_time.to_csv(root / "reports/class_by_time.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    by_time.plot.area(ax=axes[0], color=list(COLORS.values()))
    axes[0].set(title="Class counts through time", ylabel="Transactions")
    known = by_time.Illicit / (by_time.Illicit + by_time.Licit)
    axes[1].plot(known.index, known, color=COLORS[1])
    for ax in axes:
        for t in (config["train_end"] + .5, config["validation_end"] + .5): ax.axvline(t, color="black", linestyle="--", alpha=.6)
    axes[1].set(title="Illicit prevalence among labeled transactions", ylabel="Fraction", xlabel="Time step")
    save(fig, root, "class_and_time.png")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, column in zip(axes, ["total_BTC", "fees", "size"]):
        for label, name in [(2, "Licit"), (1, "Illicit")]:
            values = frame.loc[frame["class"] == label, column].dropna()
            ax.hist(np.log1p(values.clip(lower=0)), bins=50, density=True, alpha=.5, label=name, color=COLORS[label])
        ax.set(title=column, xlabel="log(1 + value)", ylabel="Density")
        ax.legend()
    save(fig, root, "transaction_distributions.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    degrees = pd.Series(dict(graph.degree())).value_counts().sort_index()
    axes[0].loglog(degrees.index[degrees.index > 0], degrees[degrees.index > 0], ".")
    axes[0].set(xlabel="Degree", ylabel="Nodes", title="Observed degree distribution (isolates omitted)")
    sizes = np.array([len(c) for c in nx.weakly_connected_components(graph)])
    axes[1].hist(sizes, bins=np.geomspace(1, max(sizes) + 1, 35))
    axes[1].set(xscale="log", yscale="log", xlabel="Component size", ylabel="Components", title="Weak component sizes")
    save(fig, root, "graph_structure.png")


def comparison(root, predictions, results, capacities):
    known = predictions[predictions.y.notna()]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for name in ["named_logistic_tx", "named_logistic_graph", "named_xgboost_tx", "named_xgboost_graph"]:
        p, r, _ = precision_recall_curve(known.y, known[name])
        axes[0].plot(r, p, label=name.replace("named_", ""))
        c = capacities[(capacities.experiment_id == name) & (capacities.scope == "all_transactions")]
        axes[1].plot(c.capacity_fraction * 100, c.recall_at_k_known, marker="o", label=name.replace("named_", ""))
    axes[0].axhline(known.y.mean(), color="gray", linestyle="--", label="Test prevalence")
    axes[0].set(xlabel="Recall", ylabel="Precision", title="Temporal test precision–recall")
    axes[1].set(xlabel="Per-step review capacity (% of ALL traffic)", ylabel="Known illicit recall", title="Unknowns also consume review capacity")
    for ax in axes: ax.legend(fontsize=8)
    save(fig, root, "model_comparison.png")
    test_results = results[results.split == "test"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.barh(test_results.experiment_id, test_results.pr_auc_ap, color="#227c9d")
    ax.set(xlabel="Average precision (AP)", title="All prespecified experiments — temporal test")
    save(fig, root, "all_experiments.png")
    by_time = pd.read_csv(root / "reports/test_by_time.csv")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for name in ["named_xgboost_tx", "named_xgboost_graph", "extended_xgboost_tx", "extended_xgboost_graph"]:
        q = by_time[by_time.experiment_id == name]
        ax.plot(q.time_step, q.ap, marker="o", label=name)
    prevalence = known.groupby("Time step").y.mean()
    ax.plot(prevalence.index, prevalence, "--", color="gray", label="Labeled prevalence")
    ax.set(xlabel="Test time step", ylabel="Average precision", title="Temporal failure is hidden by pooled performance")
    ax.legend(fontsize=8)
    save(fig, root, "temporal_generalization.png")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, name in zip(axes, ["named_xgboost_tx", "named_xgboost_graph"]):
        row = test_results[test_results.experiment_id == name].iloc[0]
        matrix = np.array([[row.tn, row.fp], [row.fn, row.tp]], dtype=int)
        ax.imshow(matrix, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(matrix[i,j]), ha="center", va="center", color="white" if matrix[i,j] > matrix.max()/2 else "black")
        ax.set(xticks=[0,1], yticks=[0,1], xticklabels=["Licit","Illicit"], yticklabels=["Licit","Illicit"],
               xlabel="Predicted", ylabel="Known label", title=name.replace("named_", ""))
    save(fig, root, "confusion_matrices.png")


def network_cases(root, frame, edges, predictions, experiment, seed=42):
    """Highest-score true/false positive and largest graph-score uplift; bounded 1-hop view."""
    cases = []
    base = "named_xgboost_tx"
    candidates = predictions.assign(uplift=predictions[experiment] - predictions[base])
    selections = []
    for name, subset, score in [
        ("high_score_illicit", candidates[candidates.y == 1], experiment),
        ("high_score_licit", candidates[candidates.y == 0], experiment),
        ("graph_uplift", candidates[candidates.y == 1], "uplift")]:
        if len(subset):
            selections.append((name, subset.sort_values([score, "txId"], ascending=[False, True]).iloc[0]))
    for name, row in selections:
        t, center = int(row["Time step"]), int(row.txId)
        visible = frame.loc[frame["Time step"] <= t].set_index("txId")
        ids = set(visible.index)
        e = edges[edges.txId1.isin(ids) & edges.txId2.isin(ids)]
        g = nx.from_pandas_edgelist(e, "txId1", "txId2", create_using=nx.DiGraph)
        g.add_node(center)
        neighbors = sorted(set(g.predecessors(center)) | set(g.successors(center)))
        selected = [center] + neighbors[:39]
        sub = g.subgraph(selected)
        pos = nx.spring_layout(sub, seed=seed)
        colors = [COLORS[int(visible.loc[v, "class"])] for v in sub]
        fig, ax = plt.subplots(figsize=(9, 6))
        nx.draw_networkx(sub, pos, ax=ax, node_color=colors, node_size=[650 if v == center else 260 for v in sub],
                         labels={v: str(v) if v == center else "" for v in sub}, font_size=8, arrows=True)
        ax.set_title(f"{name}: tx {center}, step {t}\nRed=illicit, blue=licit, gray=unknown (retrospective labels)")
        ax.axis("off")
        save(fig, root, f"case_{name}.png")
        edge_x, edge_y = [], []
        for a, b in sub.edges:
            edge_x.extend([pos[a][0], pos[b][0], None]); edge_y.extend([pos[a][1], pos[b][1], None])
        viz = go.Figure(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#aaa", width=1), hoverinfo="skip"))
        viz.add_trace(go.Scatter(x=[pos[v][0] for v in sub], y=[pos[v][1] for v in sub], mode="markers",
            marker=dict(color=colors, size=[20 if v == center else 12 for v in sub]),
            text=[f"txId={v}<br>class={visible.loc[v,'class']}<br>in={g.in_degree(v)} out={g.out_degree(v)}" for v in sub], hoverinfo="text"))
        viz.update_layout(title=f"{name} — transaction {center}; undirected visual lines, directed degrees in hover", showlegend=False)
        viz.write_html(root / "reports/figures" / f"case_{name}.html", include_plotlyjs=True)
        cases.append({"case": name, "txId": center, "time_step": t, "class": int(row["class"]),
                      "score": float(row[experiment]), "baseline_score": float(row[base]),
                      "neighbors_total": len(neighbors), "neighbors_shown": len(selected)-1})
    pd.DataFrame(cases).to_csv(root / "reports/cases.csv", index=False)
    return cases
