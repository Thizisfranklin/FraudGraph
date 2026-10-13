"""FraudGraph read-only investigation explorer.

Start with: python -m streamlit run explorer.py
No dataset download, retraining or new inference is performed.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from explorer_data import (
    capacity_at, comparison_ids, exact_row, load_reports, test_ap, test_curve,
)


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="FraudGraph | Investigation Explorer",
    page_icon="🕸️",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def get_reports():
    return load_reports(ROOT / "reports")


try:
    data = get_reports()
except (OSError, ValueError) as exc:
    st.error(f"Cannot load the committed evaluation reports: {exc}")
    st.info("Open the repository root and follow docs/EXPLORER.md.")
    st.stop()

results = data["results"]
capacities = data["review_capacity"]
timeline = data["test_by_time"]
cases = data["cases"]

st.title("FraudGraph")
st.subheader("What changes when we investigate a transaction's network?")
st.caption(
    "Interactive views of the recorded Elliptic++ experiment · "
    "End-of-time-bucket batch review · Held-out steps 40–49 · "
    "Not a live fraud detector"
)

st.info(
    "**Key finding:** Graph features improved Average Precision (AP) for the "
    "named-attribute XGBoost model, but the benefit shrank when additional "
    "transaction attributes were available. Model performance also became "
    "highly unstable in later test buckets. A good pooled score is not "
    "evidence of deployment readiness."
)

family = st.sidebar.selectbox(
    "Transaction feature set",
    options=["named", "extended"],
    format_func=lambda s: (
        "15 named attributes" if s == "named"
        else "Named + 93 anonymized attributes"
    ),
)
learner = st.sidebar.selectbox(
    "Learning algorithm", options=["xgboost", "logistic"],
    format_func=lambda s: "XGBoost" if s == "xgboost" else "Logistic regression",
)
base_id, graph_id = comparison_ids(family, learner)
base_ap = test_ap(results, base_id)
graph_ap = test_ap(results, graph_id)
delta_ap = graph_ap - base_ap

left, middle, right = st.columns(3)
left.metric("Transaction-only test AP", f"{base_ap:.4f}")
middle.metric("Transaction + graph test AP", f"{graph_ap:.4f}")
right.metric("Graph-minus-baseline AP", f"{delta_ap:+.4f}")

st.caption(
    "Average Precision (AP) evaluates ranking of **known-label** test "
    "transactions; it is not classification accuracy, a calibrated probability "
    "or the proportion of all actual illicit transactions found."
)

tab_models, tab_workload, tab_time, tab_cases = st.tabs(
    ["Model evidence", "Analyst workload", "Temporal reliability", "Selected cases"]
)

with tab_models:
    st.markdown("### Does network context actually help?")
    st.write(
        "Each pair uses the same learner and time split. The difference "
        "between the two bars is the incremental value of graph features "
        "under that feature set."
    )
    rows = []
    for f in ("named", "extended"):
        for m in ("xgboost", "logistic"):
            baseline, enhanced = comparison_ids(f, m)
            rows.append({
                "label": (
                    ("15 named" if f == "named" else "Named + 93 local")
                    + " / " + ("XGBoost" if m == "xgboost" else "Logistic")
                ),
                "baseline": test_ap(results, baseline),
                "graph": test_ap(results, enhanced),
            })
    display = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Transaction only", x=display["label"], y=display["baseline"],
        hovertemplate="%{x}<br>Test AP: %{y:.4f}<extra>Transaction only</extra>",
    ))
    fig.add_trace(go.Bar(
        name="With graph context", x=display["label"], y=display["graph"],
        hovertemplate="%{x}<br>Test AP: %{y:.4f}<extra>With graph</extra>",
    ))
    fig.update_layout(
        barmode="group", yaxis_title="Average Precision on known labels",
        xaxis_title="", yaxis_range=[0, 1], legend_title_text="Feature context",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.warning(
        "Graph features are not uniformly beneficial. In the extended "
        "XGBoost comparison the gain is small, and logistic regression "
        "performs worse with graph features. These are saved held-out "
        "results, not new experiments."
    )
    st.markdown(
        "See [the methodology walkthrough](docs/UNDERSTAND_AND_CHECK.md) "
        "and [leakage audit](reports/LEAKAGE_AUDIT.md) for model design."
    )

with tab_workload:
    st.markdown("### What if analysts can review only part of the traffic?")
    st.write(
        "Choose a precomputed capacity. At each test time bucket, the "
        "highest-ranked transactions are selected until the budget is "
        "filled. **Unknown-label transactions count toward the workload.**"
    )
    budget = st.select_slider(
        "Share of **all transactions** selected for review (per time bucket)",
        options=[1, 2, 5, 10, 20], value=5,
        format_func=lambda value: f"{value}%",
    )
    chosen = capacity_at(capacities, timeline, graph_id, budget / 100)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions reviewed", f"{chosen['reviewed']:,}")
    c2.metric("Known illicit found", f"{chosen['known_illicit']:,}")
    c3.metric(
        "Share of known illicit captured",
        f"{chosen['known_illicit_recall']:.1%}",
    )
    c4.metric("Reviewed with unknown labels", f"{chosen['unknown']:,}")
    st.caption(
        f"Known illicit denominator: {chosen['total_known_illicit']:,} across "
        "the held-out time buckets. The true rate for **all** illicit traffic "
        "cannot be calculated because most labels are unknown."
    )

    baseline_curve = test_curve(capacities, base_id)
    graph_curve = test_curve(capacities, graph_id)
    cap_fig = go.Figure()
    for label, frame in (
        ("Transaction only", baseline_curve),
        ("With graph context", graph_curve),
    ):
        cap_fig.add_trace(go.Scatter(
            x=frame["capacity_fraction"] * 100,
            y=frame["known_illicit"],
            mode="lines+markers", name=label,
            hovertemplate="Review %{x:.0f}% of traffic"
            "<br>%{y:,.0f} known illicit in queue<extra></extra>",
        ))
    cap_fig.add_vline(x=budget, line_dash="dash", opacity=0.6)
    cap_fig.update_layout(
        xaxis_title="Review capacity (% of all traffic)",
        yaxis_title="Known illicit transactions in review queue",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(cap_fig, use_container_width=True)

    breakdown_fig = go.Figure(go.Bar(
        x=["Selected review queue"] * 3,
        y=[
            chosen["known_illicit"], chosen["known_licit"],
            chosen["unknown"],
        ],
        name="Cases by available label",
        marker_color=["#b45309", "#2563eb", "#94a3b8"],
        text=[
            f"Known illicit: {chosen['known_illicit']:,}",
            f"Known licit: {chosen['known_licit']:,}",
            f"Unknown: {chosen['unknown']:,}",
        ],
        textposition="inside",
    ))
    # A single stacked column needs separate traces for a meaningful legend.
    breakdown_fig = go.Figure()
    for label, count in (
        ("Known illicit", chosen["known_illicit"]),
        ("Known licit", chosen["known_licit"]),
        ("Unknown", chosen["unknown"]),
    ):
        breakdown_fig.add_trace(go.Bar(
            x=["Selected review queue"], y=[count], name=label,
            hovertemplate=f"{label}: %{{y:,.0f}}<extra></extra>",
        ))
    breakdown_fig.update_layout(
        barmode="stack", yaxis_title="Transactions reviewed",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(breakdown_fig, use_container_width=True)
    st.caption(
        "This is a **top-K workload constraint**, not the fixed-score LOW / "
        "REVIEW / HIGH banding policy. No cost, loss avoided, or analyst "
        "time has been estimated. See reports/DECISION_FRAMEWORK.md."
    )

with tab_time:
    st.markdown("### Do pooled model results hide a reliability problem?")
    st.write(
        "The points show AP evaluated separately in each of the 10 future "
        "test buckets. Each bucket contains a different number and mix "
        "of known outcomes."
    )
    fig = go.Figure()
    for label, experiment in (
        ("Transaction only", base_id),
        ("With graph context", graph_id),
    ):
        segment = timeline.loc[
            timeline["experiment_id"] == experiment
        ].sort_values("time_step")
        fig.add_trace(go.Scatter(
            x=segment["time_step"], y=segment["ap"],
            mode="lines+markers", name=label,
            customdata=segment[["labeled", "illicit"]].to_numpy(),
            hovertemplate=(
                "Step %{x}<br>AP %{y:.4f}<br>Known-label count %{customdata[0]:,.0f}"
                "<br>Known illicit %{customdata[1]:,.0f}<extra></extra>"
            ),
        ))
    fig.update_layout(
        yaxis_title="AP within time bucket (known labels)",
        xaxis_title="Held-out time step", yaxis_range=[0, 1],
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    context = timeline.loc[
        timeline["experiment_id"] == graph_id
    ].sort_values("time_step").copy()
    context["prevalence"] = 100 * context["illicit"] / context["labeled"]
    fig2 = go.Figure(go.Bar(
        x=context["time_step"], y=context["prevalence"],
        hovertemplate="Step %{x}<br>Known illicit prevalence %{y:.2f}%<extra></extra>",
    ))
    fig2.update_layout(
        xaxis_title="Held-out time step",
        yaxis_title="Illicit share among known labels (%)",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.warning(
        "The late-period decline is real in these saved test summaries, "
        "but the cause is not established. Changes in class prevalence, "
        "population composition and label availability complicate AP "
        "comparisons. This demo does not claim to diagnose drift."
    )

with tab_cases:
    st.markdown("### Three saved examples — not a searchable case database")
    descriptions = {
        "graph_uplift": "Illicit example: larger score after graph features",
        "high_score_illicit": "Known-illicit example: high score",
        "high_score_licit": "Known-licit example: high score (review friction)",
    }
    chosen_key = st.selectbox(
        "Illustrative case", options=list(descriptions),
        format_func=descriptions.get,
    )
    record = exact_row(cases, case=chosen_key)
    tx_score = float(record["baseline_score"])
    graph_score = float(record["score"])
    a, b, c = st.columns(3)
    a.metric("Transaction only (model score)", f"{tx_score:.3f}")
    b.metric("Transaction + graph (model score)", f"{graph_score:.3f}")
    c.metric("Change in score", f"{graph_score-tx_score:+.3f}")
    label = {
        1: "Known illicit", 2: "Known licit",
    }.get(int(record["class"]), "Unknown")
    st.write(
        f"**Transaction ID:** {int(record['txId'])} · "
        f"**Time step:** {int(record['time_step'])} · "
        f"**Dataset label:** {label} · "
        f"**Observed neighbors:** {int(record['neighbors_total'])}"
    )
    st.caption(
        "Scores from two different fitted models are **not calibrated "
        "probabilities**. A high score does not prove legal guilt, and "
        "these handpicked cases do not establish typical behavior."
    )
    if chosen_key == "graph_uplift":
        figure_path = ROOT / "reports/figures/case_graph_uplift.png"
        if figure_path.is_file():
            st.image(str(figure_path), caption=(
                "Saved, one-hop neighborhood illustration; "
                "not a live or complete blockchain explorer."
            ))
        else:
            st.info("The committed case figure is unavailable in this checkout.")
    st.write(
        "For full interpretation, read the source cases and "
        "[the case-study walkthrough](docs/UNDERSTAND_AND_CHECK.md)."
    )

st.divider()
st.caption(
    "Independent research demonstration using published Elliptic++ data. "
    "All statistics are loaded from committed evaluation artifacts. "
    "Labels are incomplete; no new risk scores, customer identity, "
    "blocked transactions or financial benefit are claimed."
)
