# FraudGraph Investigator (React)

A human-in-the-loop **Bitcoin transaction investigation workbench**, built with React, React Flow, Vite, and Recharts.

This application is a **retrospective research demo**, not a fraud verdict engine. It displays actual Elliptic++ transaction examples, saved XGBoost scores from the original FraudGraph experiment, bounded directed graph neighborhoods, historical outcomes where known, and a few original SHAP contributions.

## Features

- Search and filter a review queue of real saved dataset transaction examples by ID, time step and known/unknown label.
- Click a transaction to compare transaction-only versus graph-enhanced XGBoost scores.
- Pan, zoom and inspect its real directed one-hop network (React Flow) with class labels clearly marked retrospective.
- Inspect original, recorded SHAP model contributions for the three published illustrative cases. No invented SHAP results for other samples.
- Explore historical ranking AP by time step, the drop around step 43, label prevalence, hypothetical delay scenarios, and analyst review-capacity tradeoffs.
- Save analyst notes in this browser (localStorage); export a versioned JSON case report locally.
- Responsive dark UI suitable for desktop and mobile.

## Run the app locally

Requires Node.js 20+.

```bash
cd app
npm install
npm run dev
```

Visit the local URL displayed by Vite (normally http://localhost:5173).

There are three bundled **verified** source-backed cases, even if the larger dataset has not been generated. For a richer queue and interactive directed neighborhoods, run the export job (below) and place the generated `investigations.json` into `app/public/`.

## Export genuine additional cases (never synthetic)

From the repository root with Python 3.12 and dependencies:

```bash
pip install -r requirements.txt
pip install --no-deps -e .
python -m fraudgraph.pipeline --download
python scripts/export_investigator_samples.py
```

The exporter selects only **real saved test predictions**, retains unknown labels, adds actual graph edges visible at the end of each case's time step, and checks that the three published case scores exactly match the saved case artifacts.

The GitHub Actions workflow **Build real Investigator case data** builds `investigations.json` as a downloadable artifact. Keep a copy of the exported dataset in `app/public` to make the full sample queue available to visitors.

## Build and deploy

```bash
cd app
npm run build
npm run preview
```

The repository also includes a GitHub Actions workflow to run the React production build and publish to GitHub Pages on the `main` branch. If your repository has not enabled Pages, configure **Settings → Pages → Build and deployment → Source: GitHub Actions**. The site will then be served from `https://thizisfranklin.github.io/FraudGraph/`.

## Model, scope and limitations

- **Scores in case views:** Frozen historical `named_xgboost_graph` and `named_xgboost_tx` scores, created in the original FraudGraph experiment. These are **not** calibrated probabilities.
- **Research candidate:** Later forward validations under a hypothetical **2-bucket label delay** selected expanding-history XGBoost with max_depth=3, n_estimators=150, learning_rate=.05 (mean AP 0.8140; worst-period AP 0.7503 across validation steps 35/37/39). This is **not** a prospectively validated production model and is not silently swapped into the saved case scores.
- **Dataset scope:** Elliptic++ nodes are Bitcoin transactions; an arbitrary live Bitcoin transaction hash or wallet address cannot be checked by this interface. Dataset IDs are anonymized.
- **Data availability:** Some outcomes are unknown; treat them as **unknown**, not licit. Graph relationships are observable at the **end** of the time bucket, not necessarily at the moment of a transaction.
- **Decision scope:** Analyst investigation support only. The app makes no criminality, identity, account-blocking, or monetary-harm determination.
- **Evaluation limitation:** Steps 40-49 informed the subsequent drift/regularization research design. A truly new later period is needed for independent confirmation.

See [the project's reproducibility and robustness study](../docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md), [feature dictionary](../reports/FEATURE_DICTIONARY.md), [case records](../reports/cases.csv), and [original dataset reference](https://github.com/git-disl/EllipticPlusPlus).
