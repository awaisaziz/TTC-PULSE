#!/usr/bin/env bash
set -euo pipefail

DB_PATH="data/ttc.duckdb"

if ! command -v duckdb >/dev/null 2>&1; then
  echo "ERROR: duckdb CLI is not installed or not on PATH."
  echo "Install DuckDB CLI, then rerun: scripts/setup_duckdb.sh"
  exit 1
fi

mkdir -p data
mkdir -p data/parquet

echo "[1/2] Initializing base objects in ${DB_PATH}"
duckdb "${DB_PATH}" < sql/duckdb/01_initialize.sql

echo "[2/2] Creating optimized views"
duckdb "${DB_PATH}" < sql/duckdb/02_optimized_views.sql

echo "Done. Run example filters with:"
echo "  duckdb ${DB_PATH} < sql/duckdb/03_filter_queries.sql"
