# SQL

## Purpose
The `sql/` folder contains DuckDB SQL scripts that create and optimize the analytics layer used by the backend API.

## What is in this folder
- `duckdb/01_initialize.sql` — base initialization: reads raw CSVs, writes parquet lake, defines `delays` view, loads GTFS dimension tables.
- `duckdb/02_optimized_views.sql` — optimized summary views (`route_delay_summary`, `hourly_pattern`, `hotspot_routes`).
- `duckdb/03_filter_queries.sql` — parameterized query templates and pruning example.

## Core SQL files and why they matter
1. `duckdb/01_initialize.sql` — foundation of the whole analytics dataset.
2. `duckdb/02_optimized_views.sql` — performance-friendly views used for analytics exploration.
3. `duckdb/03_filter_queries.sql` — reusable query patterns for route/time/type filters.

## Run only the SQL layer
From repo root:

```bash
./scripts/setup_duckdb.sh
```

Manual execution:

```bash
duckdb data/ttc.duckdb < sql/duckdb/01_initialize.sql
duckdb data/ttc.duckdb < sql/duckdb/02_optimized_views.sql
```

Run sample filter queries:

```bash
duckdb data/ttc.duckdb < sql/duckdb/03_filter_queries.sql
```
