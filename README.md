# FraudGraph

> Graph-based fraud analytics — modeling fraud as a network problem, not just a transaction problem.

[![Status](https://img.shields.io/badge/status-active%20development-blue)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The Problem

Traditional fraud detection looks at individual transactions in isolation. But fraud rarely happens in isolation.

A compromised account shares a device with three others. Two flagged payment methods resolve to the same IP address. A cluster of new users all registered within minutes of each other, from the same subnet.

These patterns are invisible at the transaction level. They become visible as a graph.

**FraudGraph** builds a connected representation of users, devices, payment methods, IP addresses, and transactions — then mines that network for the kind of structural signals that isolated transaction analysis can't see.

---

## What This Project Explores

- **Entity relationship modeling** — representing transactional data as a graph of interconnected entities
- **Graph feature engineering** — deriving risk signals from network structure (centrality, clustering, community detection)
- **Risk scoring** — building interpretable, prioritized risk scores from graph-derived features
- **Investigation tooling** — designing analyst-facing dashboards and interactive network visualizations
- **Realistic synthetic data** — generating and validating data with credible relationship complexity, noise, and fraud pattern representation

---

## Architecture

```
Transactional Data
        │
        ▼
Entity Resolution
(User · Device · IP · Payment Method)
        │
        ▼
Graph Construction
        │
        ├──────────────────────────────────┐
        ▼                                  ▼
Graph Feature Engineering           Community Detection
(Degree, Centrality, Clustering)    (Louvain, Label Propagation)
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
               Risk Scoring Layer
                       │
                       ▼
           Investigation Dashboard
                       │
                       ▼
      Interactive Network Visualization
```

---

## Why Graph Analytics for Fraud?

Fraudsters exploit the gaps between siloed data systems. A device shared across ten accounts is a transaction-level blind spot — but in a graph, it's a high-degree node connecting otherwise unrelated entities. The same logic applies to shared IPs, shared payment instruments, and coordinated account creation.

Graph analytics surfaces these structural patterns by treating the *relationships* between entities as first-class signals, alongside the raw transaction attributes.

Key graph-derived signals this project explores:

| Signal | What it captures |
|---|---|
| Node degree | How many other entities is this one connected to? |
| Betweenness centrality | Is this entity a bridge between otherwise separate clusters? |
| Clustering coefficient | Are an entity's neighbors tightly interconnected? |
| Community membership | Does this entity belong to a suspiciously dense subgraph? |
| Shared resource risk | Is a device, IP, or payment method shared across flagged entities? |

---

## Tech Stack

**Analytics & Modeling**
- Python · Pandas · NumPy · Scikit-learn

**Graph Analytics**
- NetworkX · Neo4j AuraDB

**Visualization & Dashboards**
- Streamlit · Plotly · Pyvis

**Development**
- Git · GitHub · Jupyter Notebook

---

## Project Status

🚧 **Active Development**

| Phase | Status |
|---|---|
| Synthetic data generation & validation | 🔄 In progress |
| Entity resolution & graph construction | 🔄 In progress |
| Graph feature engineering | 📋 Planned |
| Risk scoring methodology | 📋 Planned |
| Investigation dashboard | 📋 Planned |
| Interactive network visualization | 📋 Planned |

---

## A Note on Synthetic Data

This project uses synthetic data generated for experimentation and learning.

A known failure mode in synthetic fraud datasets is being *too clean* — perfectly balanced classes, no noise, unrealistically tidy relationship structures. A model trained on such data may perform well on paper while learning patterns that don't exist in real environments.

Development here includes explicit validation of:

- Relationship realism (do shared devices/IPs occur at plausible rates?)
- Class distribution (is the fraud rate representative of real-world baselines?)
- Network complexity (are graph structures sufficiently varied and non-trivial?)
- Noise and variability (are there false positives, ambiguous cases, behavioral drift?)
- Fraud pattern representation (do synthetic fraud clusters resemble known real-world patterns?)

The goal is not to build a model that performs well on synthetic data. The goal is to build an approach that *could* hold up under more realistic conditions.

---

## Repository Structure

```
fraudgraph/
├── data/
│   ├── raw/                  # Synthetic transaction records
│   └── processed/            # Entity-resolved, graph-ready datasets
├── notebooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_graph_construction.ipynb
│   ├── 03_feature_engineering.ipynb
│   └── 04_risk_scoring.ipynb
├── src/
│   ├── data/                 # Data generation and entity resolution
│   ├── graph/                # Graph construction and feature extraction
│   ├── scoring/              # Risk scoring logic
│   └── dashboard/            # Streamlit app
├── tests/
├── requirements.txt
└── README.md
```

---

## Future Directions

- Near real-time risk scoring pipelines
- Graph embeddings and representation learning (Node2Vec, GraphSAGE)
- Unsupervised anomaly detection on graph structure
- Explainability features for investigation workflows
- Evaluation on larger, more complex graph topologies

---

## About

Building as a portfolio project exploring the intersection of graph analytics and fraud detection. Motivated by the observation that fraud often leaves structural footprints in relationship data that transaction-level analysis alone can't capture.

Questions, feedback, or collaboration — feel free to open an issue or reach out.
