-- Optional PostgreSQL deployment schema; analytical queries also execute in SQLite.
CREATE TABLE transactions (
    tx_id BIGINT PRIMARY KEY, time_step INTEGER NOT NULL CHECK (time_step BETWEEN 1 AND 49),
    class INTEGER NOT NULL CHECK (class IN (1,2,3)), total_btc DOUBLE PRECISION, fees DOUBLE PRECISION
);
CREATE TABLE edges (
    source BIGINT REFERENCES transactions(tx_id), target BIGINT REFERENCES transactions(tx_id),
    PRIMARY KEY (source, target)
);
CREATE INDEX edges_target_idx ON edges(target);
CREATE TABLE risk_scores (
    tx_id BIGINT PRIMARY KEY REFERENCES transactions(tx_id), class INTEGER NOT NULL,
    score DOUBLE PRECISION NOT NULL, risk_band TEXT NOT NULL CHECK (risk_band IN ('LOW','REVIEW','HIGH'))
);
