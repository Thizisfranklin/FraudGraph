-- Portable to PostgreSQL and SQLite. Tables are exported by the pipeline.
-- Unknown class 3 remains separate. Labels are only used in retrospective reports.
SELECT time_step, class, COUNT(*) AS transactions,
       AVG(total_btc) AS mean_btc, AVG(fees) AS mean_fee
FROM transactions GROUP BY time_step, class ORDER BY time_step, class;

-- Edge endpoint audit; joins must preserve the entire edge table.
SELECT a.time_step AS source_step, b.time_step AS target_step, COUNT(*) AS edges
FROM edges e JOIN transactions a ON e.source = a.tx_id
JOIN transactions b ON e.target = b.tx_id
GROUP BY a.time_step, b.time_step ORDER BY source_step, target_step;

-- Observed incoming relationships at the end of each target time bucket.
SELECT b.tx_id, COUNT(a.tx_id) AS visible_in_degree
FROM transactions b LEFT JOIN edges e ON b.tx_id = e.target
LEFT JOIN transactions a ON a.tx_id = e.source AND a.time_step <= b.time_step
GROUP BY b.tx_id ORDER BY b.tx_id;

-- Review load and known/unknown label composition: no imputed ground truth.
SELECT risk_band, COUNT(*) AS volume,
       SUM(CASE WHEN class = 1 THEN 1 ELSE 0 END) AS known_illicit,
       SUM(CASE WHEN class = 2 THEN 1 ELSE 0 END) AS known_licit,
       SUM(CASE WHEN class = 3 THEN 1 ELSE 0 END) AS unknown
FROM risk_scores GROUP BY risk_band ORDER BY risk_band;
