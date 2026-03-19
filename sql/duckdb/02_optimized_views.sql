-- Optimized analytical views.

CREATE OR REPLACE VIEW route_delay_summary AS
SELECT
    d.route_id,
    AVG(d.min_delay)::DOUBLE AS avg_delay,
    COUNT(*)::BIGINT AS count,
    quantile_cont(d.min_delay, 0.90)::DOUBLE AS p90_delay
FROM delays d
GROUP BY d.route_id;

CREATE OR REPLACE VIEW hourly_pattern AS
SELECT
    EXTRACT('hour' FROM d.service_time)::INTEGER AS hour,
    d.route_id,
    AVG(d.min_delay)::DOUBLE AS avg_delay
FROM delays d
GROUP BY 1, 2;

CREATE OR REPLACE VIEW hotspot_routes AS
SELECT
    d.route_id,
    d.vehicle_type,
    AVG(d.min_delay)::DOUBLE AS avg_delay,
    COUNT(*)::BIGINT AS event_count,
    quantile_cont(d.min_delay, 0.90)::DOUBLE AS p90_delay
FROM delays d
GROUP BY d.route_id, d.vehicle_type
HAVING COUNT(*) >= 100
ORDER BY avg_delay DESC, p90_delay DESC
LIMIT 25;
