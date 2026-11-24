"""Build an offline, read-only interactive HTML research report with Plotly.

This is an interpretability/analysis aid, NOT a live Bitcoin fraud classifier.
Unknown labels remain unknown, and scores do not establish legal wrongdoing.
"""
from pathlib import Path
import argparse
import html

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]


def read_optional(folder, name):
    path = folder / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def make_dashboard(root=ROOT):
    folder = root / "reports/exploratory"
    folds = read_optional(folder, "regularization_validation_folds.csv")
    selected = read_optional(folder, "regularization_selected_per_lag.csv")
    capacity = read_optional(folder, "capacity_validation.csv")
    if folds.empty or selected.empty or capacity.empty:
        raise FileNotFoundError(
            "Run python scripts/run_robustness_research.py first; validation CSVs are required."
        )

    sections = []
    first_figure = True

    def append_plot(title, fig, note):
        nonlocal first_figure
        part = fig.to_html(full_html=False, include_plotlyjs=True if first_figure else False,
                           config={"responsive": True, "displaylogo": False})
        first_figure = False
        sections.append(
            '<section class="panel"><h2>' + html.escape(title) + '</h2>'
            '<p>' + html.escape(note) + '</p>' + part + '</section>'
        )

    # Comparing in-sample and forward AP shows model complexity and data shift;
    # it does not independently diagnose classical overfitting.
    fig = go.Figure()
    shown = folds.groupby(["capacity_preset", "strategy"], as_index=False).agg(
        train_ap=("train_ap_in_sample", "mean"),
        forward_ap=("forward_ap", "mean"),
    )
    for strategy, part in shown.groupby("strategy", sort=True):
        fig.add_trace(go.Scatter(
            x=part.train_ap, y=part.forward_ap,
            mode="markers+text", name=strategy, text=part.capacity_preset,
            textposition="top center",
            hovertemplate="Train AP: %{x:.3f}<br>Forward AP: %{y:.3f}<extra>" +
                          str(strategy) + "</extra>"
        ))
    fig.update_layout(xaxis_title="Training AP (optimistic / in sample)",
                      yaxis_title="Future-period validation AP",
                      height=510, margin=dict(l=50, r=20, t=30, b=65))
    append_plot("Model capacity: memorization versus generalization", fig,
                "Complex models can have high training AP and still fail on later periods. "
                "Differences also reflect time drift and label prevalence, so a gap alone is not proof of overfitting.")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=selected.label_lag.astype(str),
        y=selected.mean_forward_ap,
        name="Mean validation AP",
        text=selected.candidate,
        textposition="auto",
    ))
    fig.add_trace(go.Bar(
        x=selected.label_lag.astype(str),
        y=selected.worst_forward_ap,
        name="Worst-period validation AP",
    ))
    fig.update_layout(
        barmode="group", height=460,
        xaxis_title="Assumed delay until labels mature (time buckets)",
        yaxis_title="Average Precision",
        margin=dict(l=50, r=20, t=30, b=70)
    )
    append_plot("Label availability: 2-, 4- and 6-bucket scenarios", fig,
                "The best strategy is selected separately for each lag scenario. "
                "The label delay represents a hypothetical availability constraint, not something to optimize for accuracy.")

    # Analyst review budget: include unknowns in traffic/denominator.
    fig = go.Figure()
    for lag, part in capacity.groupby("label_lag", sort=True):
        budget = part.groupby("capacity_fraction", as_index=False).agg(
            mean_capture=("known_illicit_capture", "mean"),
        )
        fig.add_trace(go.Scatter(
            x=budget.capacity_fraction * 100, y=budget.mean_capture * 100,
            mode="lines+markers", name=f"Label lag {lag}"
        ))
    fig.update_layout(height=450, xaxis_title="Analyst review capacity (% of all transactions)",
                      yaxis_title="Mean captured known illicit (%)",
                      yaxis_range=[0, 100], margin=dict(l=50, r=20, t=30, b=70))
    append_plot("Analyst budget: known-illicit capture at 1%, 5%, 10%", fig,
                "Unknown-label cases consume a review slot. Capture is measured among KNOWN illicit "
                "transactions, not all illicit activity. Lines average three validation periods equally.")

    feature_drift = read_optional(folder, "feature_drift_by_time.csv")
    if not feature_drift.empty:
        fig = go.Figure()
        for feature in ("size", "fees", "g_pagerank_scaled", "g_component_size"):
            subset = feature_drift.loc[feature_drift.feature == feature]
            if not subset.empty:
                fig.add_trace(go.Scatter(x=subset.time_step, y=subset.psi,
                                         mode="lines+markers", name=feature))
        fig.add_vline(x=43, line_dash="dash", line_color="gray")
        fig.update_layout(height=450, xaxis_title="Time step",
                          yaxis_title="Population Stability Index (reference: steps 1-29)",
                          margin=dict(l=50, r=20, t=30, b=70))
        append_plot("Input drift: which features move over time?", fig,
                    "PSI is unsupervised. Large PSI can also reflect time-bucket signatures; "
                    "it does NOT prove fraud concept drift or causation.")

    labels = read_optional(folder, "label_score_drift_by_time.csv")
    if not labels.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=labels.time_step, y=labels.average_precision_labeled,
            name="Original-model AP", mode="lines+markers"))
        fig.add_trace(go.Scatter(
            x=labels.time_step, y=labels.known_illicit_prevalence,
            name="Known-illicit prevalence", mode="lines+markers"))
        fig.add_vline(x=43, line_dash="dash", line_color="gray")
        fig.update_layout(height=440, xaxis_title="Time step",
                          yaxis_title="AP / Fraction", margin=dict(l=50, r=20, t=30, b=70))
        append_plot("The step-43 collapse in context", fig,
                    "Only labeled outcomes enter AP and prevalence; label coverage and labeling policy "
                    "may also change. This cannot establish concept drift on its own.")

    post = read_optional(folder, "regularization_posthoc_test.csv")
    if not post.empty:
        fig = go.Figure()
        for lag, part in post.groupby("label_lag", sort=True):
            fig.add_trace(go.Scatter(
                x=part.time_step, y=part.forward_ap,
                mode="lines+markers", name=f"Post-hoc replay (lag {lag})"))
        fig.update_layout(height=480, xaxis_title="Previously inspected test time step",
                          yaxis_title="Average Precision",
                          margin=dict(l=50, r=20, t=30, b=65))
        append_plot("Exploratory later-period replay — NOT an untouched test", fig,
                    "The project already examined steps 40-49. These lines are exploratory and must not "
                    "be claimed as independent model generalization evidence.")

    output = folder / "analyst_research_review.html"
    markup = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FraudGraph | Temporal model research</title>
<style>
:root{color-scheme:light}body{font:16px/1.65 system-ui,-apple-system,sans-serif;
background:#f4f7fa;color:#142337;max-width:1190px;margin:auto;padding:26px}
header{padding:28px;border-radius:14px;background:#152b45;color:white}
header p{color:#d9e4ed}h1{font-size:2rem;margin:0}h2{font-size:1.25rem;margin:.15rem 0}
.panel{background:white;border-radius:12px;padding:24px;margin-top:20px;
box-shadow:0 1px 6px #152b4514}.panel p{color:#40556b;margin-top:4px}
.notice{margin-top:16px;padding:14px;border-left:4px solid #d89b24;background:#fff8e9}
small{color:#65758a}footer{margin:26px 0}</style></head><body>
<header><h1>FraudGraph · Temporal Model Research</h1>
<p>A visual investigation into changing Bitcoin transaction patterns, model complexity,
label delays, and analyst review capacity.</p></header>
<div class="notice"><strong>Research use only.</strong> This is NOT a real-time fraud
detector or evidence of wrongdoing. Known outcomes are incomplete, scores are
uncalibrated, and test-period replay is retrospective. Explore patterns, do not
automatically block transactions.</div>
""" + "\n".join(sections) + """
<footer><small>All figures are generated from saved local research CSVs.
Offline Plotly is embedded. For protocol and caveats see
docs/TEMPORAL_DRIFT_STUDY.md and docs/ANALYST_WORKBENCH_ROADMAP.md.</small></footer>
</body></html>"""
    output.write_text(markup, encoding="utf-8")
    print("Wrote interactive read-only report:", output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    make_dashboard(args.root.resolve())


if __name__ == "__main__":
    main()
