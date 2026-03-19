#!/usr/bin/env bash
set -euo pipefail

DB_PATH="data/ttc.duckdb"

if ! command -v duckdb >/dev/null 2>&1; then
  echo "ERROR: duckdb CLI is not installed or not on PATH."
  exit 1
fi

if [[ ! -f "${DB_PATH}" ]]; then
  echo "ERROR: ${DB_PATH} not found. Run scripts/setup_duckdb.sh first."
  exit 1
fi

echo "[check] connection"
duckdb "${DB_PATH}" -c "SELECT 'connected' AS status;"

echo "[check] aggregation sanity"
duckdb "${DB_PATH}" -c "
SELECT
  (SELECT COUNT(*) FROM route_delay_summary) AS summary_rows,
  (SELECT COUNT(*) FROM hourly_pattern) AS hourly_rows,
  (SELECT COUNT(*) FROM hotspot_routes) AS hotspot_rows;
"

echo "[check] explain analyze for partition pruning"
duckdb "${DB_PATH}" -c "EXPLAIN ANALYZE SELECT AVG(min_delay) FROM delays WHERE vehicle_type='bus' AND year=2024 AND month=1;"

echo "[check] runtime targets"
/usr/bin/time -f 'elapsed=%e s' duckdb "${DB_PATH}" -c "SELECT route_id, AVG(min_delay) FROM delays WHERE vehicle_type='bus' AND year=2024 AND month=1 GROUP BY route_id LIMIT 20;" >/dev/null
/usr/bin/time -f 'elapsed=%e s' duckdb "${DB_PATH}" -c "SELECT * FROM hotspot_routes LIMIT 10;" >/dev/null
