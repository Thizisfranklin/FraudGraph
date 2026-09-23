# Repository audit

The starting `main` branch contained one tracked file: `README.md`. There were no scripts, notebooks, datasets, dependencies, tests, or separate project specification. The README was a proposal, with no measured results. Its original version remains in Git history.

The implementation preserves the core transaction-versus-graph question. It narrows the claims to Bitcoin transactions: the supplied data does not establish device/IP/payment-instrument fraud detection. The wallet graph, Neo4j, and a GNN are omitted because they are not needed for the classical experiment. SQL is executed in SQLite; PostgreSQL-compatible schema and queries are supplied without claiming a PostgreSQL server was run.

The source data is the transaction subset from the authors' `git-disl/EllipticPlusPlus` repository at commit `08fe6aded83afb97bf5a79a71130f542ca783c2e`. The reproducible downloader fetches only the three required transaction CSVs and checks their Git LFS SHA-256 object hashes. Raw data, trained models, and bulky intermediate tables stay out of Git.

Architecture: a small installable `fraudgraph` package owns computation; seven executed notebooks explain and inspect its persisted outputs. This avoids seven divergent copies of the modeling code. JSON configuration defines the temporal boundaries, seed, thread limit, and policy scenario. An append-only experiment ledger records all completed experiments, including sensitivity results.
