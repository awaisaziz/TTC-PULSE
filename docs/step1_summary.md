# Step 1 Summary

Generated (UTC): 2026-03-17T20:01:13Z

Step 1 scope completed: Raw + Bronze + DuckDB foundation only.

## Completed

- Project structure scaffolded for TTC Pulse MVP.
- DuckDB database created at `data/ttc_pulse.duckdb`.
- Immutable raw registries created and registered in DuckDB.
- Bronze row-preserving tables with lineage columns created and exported to Parquet.
- GTFS-RT Bronze entity table created as schema-ready shell (polling deferred).
- Ingestion logs and source inventory generated locally.

## Raw Registry Tables

| Table | Rows |
|---|---:|
| `raw_bus_delay_events_registry` | 100 |
| `raw_subway_delay_events_registry` | 61 |
| `raw_gtfs_static_files_registry` | 8 |
| `raw_gtfsrt_alert_snapshots_registry` | 0 |

## Bronze Tables

| Table | Rows |
|---|---:|
| `bronze_bus_events` | 776435 |
| `bronze_subway_events` | 250558 |
| `bronze_gtfsrt_alert_entities` | 0 |
| `bronze_gtfs_agency` | 1 |
| `bronze_gtfs_calendar` | 8 |
| `bronze_gtfs_calendar_dates` | 7 |
| `bronze_gtfs_routes` | 229 |
| `bronze_gtfs_shapes` | 1025672 |
| `bronze_gtfs_stop_times` | 4249149 |
| `bronze_gtfs_stops` | 9417 |
| `bronze_gtfs_trips` | 133665 |

## Exclusions

- Silver/Gold/dashboard work not started in this step.
- Streetcar ingestion excluded from core MVP scope.
- GTFS-RT polling DAG execution deferred.

## Output Files

- `raw/` registries (CSV + Parquet)
- `bronze/` table exports (Parquet)
- `configs/schema_bus.yml`
- `configs/schema_subway.yml`
- `docs/source_inventory.md`
- `logs/ingestion_log.csv`
- `docs/step1_summary.md`
