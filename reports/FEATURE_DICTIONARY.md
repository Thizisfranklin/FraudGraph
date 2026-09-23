# Feature dictionary

## Named transaction baseline (15 columns)

| Column(s) | Interpretation and availability |
|---|---|
| `total_BTC` | Source-provided transaction BTC amount; unscaled units from source |
| `fees` | Transaction fee in BTC |
| `size` | Transaction size in bytes |
| `num_input_addresses`, `num_output_addresses` | Address counts intrinsic to the transaction |
| `in_BTC_min/max/mean/median/total` | Five source-provided summaries of input BTC amounts |
| `out_BTC_min/max/mean/median/total` | Five source-provided summaries of output BTC amounts |

The slash notation expands to five real columns in each row. These values are assumed observable once the transaction is observed. Missing values use training medians, not class-specific or full-dataset values. Source definitions should not be interpreted more precisely than the released column names allow.

## Engineered graph context (8 columns)

All features use the directed observed subgraph induced by transactions whose time is at or before the scored bucket. Each transaction's features are frozen at that bucket's close. None use class labels.

| Column | Definition | Why it may help |
|---|---|---|
| `g_in_degree` | Number of observed predecessor transactions | Incoming fan-in pattern |
| `g_out_degree` | Number of observed successor transactions | Outgoing fan-out pattern |
| `g_total_degree` | Sum of directed in/out degree | Connectivity intensity; redundant by design for a linear model |
| `g_pagerank_scaled` | PageRank with damping 0.85, multiplied by snapshot node count | Relative flow centrality without a mechanically shrinking scale |
| `g_component_size` | Number of nodes in the weakly connected component | Whether activity sits in a small chain or larger structure |
| `g_component_density` | Directed edge count / [n(n−1)]; zero for singleton | Component connectivity adjusted for size |
| `g_neighbor_degree_mean` | Mean total directed degree of unique immediate neighbors; zero if none | Whether the transaction adjoins hubs |
| `g_reciprocal_fraction` | Number of neighbors connected in both directions / unique neighbors; zero if none | Reciprocal structure diagnostic; can be constant in transaction DAGs |

Constant/redundant features are reported rather than misrepresented as predictive signals. PageRank convergence is checked by NetworkX, and nonfinite feature values fail validation. No all-pairs paths, betweenness, or expensive community search is needed.

## Sensitivity and exclusions

`Local_feature_1` through `Local_feature_93` extend the named baseline in the sensitivity experiments. They are anonymized local features provided by the authors, not reverse-engineered financial quantities. `Aggregate_feature_1` through `Aggregate_feature_72` and supplied `in_txs_degree` / `out_txs_degree` are excluded from every experiment. `class`, `y`, `txId`, and `Time step` are never predictors. Exact per-experiment lists are saved in `feature_sets.json`.
