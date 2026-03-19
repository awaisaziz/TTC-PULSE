-- Query templates with partition-pruning friendly predicates.
-- Replace ? placeholders using your client parameter syntax.

-- 1) Filter by route.
SELECT
    service_date,
    service_time,
    route_id,
    vehicle_type,
    min_delay
FROM delays
WHERE route_id = ?
ORDER BY service_date DESC, service_time DESC
LIMIT 200;

-- 2) Filter by time window (uses year/month + date to maximize pruning).
SELECT
    route_id,
    vehicle_type,
    AVG(min_delay)::DOUBLE AS avg_delay,
    COUNT(*)::BIGINT AS events
FROM delays
WHERE year = ?
  AND month BETWEEN ? AND ?
  AND service_date BETWEEN ? AND ?
GROUP BY route_id, vehicle_type
ORDER BY avg_delay DESC
LIMIT 50;

-- 3) Filter by vehicle type (direct partition filter).
SELECT
    route_id,
    AVG(min_delay)::DOUBLE AS avg_delay,
    quantile_cont(min_delay, 0.90)::DOUBLE AS p90_delay,
    COUNT(*)::BIGINT AS event_count
FROM delays
WHERE vehicle_type = ?
GROUP BY route_id
ORDER BY avg_delay DESC
LIMIT 25;

-- Optional: prove partition pruning in your environment.
EXPLAIN ANALYZE
SELECT AVG(min_delay)
FROM delays
WHERE vehicle_type = 'bus'
  AND year = 2024
  AND month = 1;
