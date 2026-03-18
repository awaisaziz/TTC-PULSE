# Silver Layer

Generated: 2026-03-17 (America/New_York)

## Purpose

Silver is the canonical normalization layer for TTC Pulse Step 2. It standardizes bus, subway, and GTFS-RT alert entities while preserving lineage and adding linkage metadata.

## Implemented Silver Tables

| Table | Rows | Role |
|---|---:|---|
| `silver_bus_events` | 776435 | Canonical bus events (route-first) |
| `silver_subway_events` | 250558 | Canonical subway events (station-first) |
| `silver_gtfsrt_alert_entities` | 0 | Canonical GTFS-RT alert entities shell |
| `fact_delay_events_norm` | 1026993 | Unified delay fact for bus + subway |
| `fact_gtfsrt_alerts_norm` | 0 | Canonical GTFS-RT alert fact |

## Canonical Columns

Common canonical fields in Silver/facts include:
- `event_id` / `alert_entity_id`
- normalized route/station keys (`route_key`, `station_key`)
- core metrics (`delay_minutes`, `gap_minutes`)
- linkage fields (`match_method`, `match_confidence`, `link_status`)
- lineage fields (`lineage_source_file`, `lineage_source_row_number`, `lineage_bronze_loaded_at_utc`, `lineage_source_registry`)

## Persistence Contract

- Tables are registered in DuckDB (`data/ttc_pulse.duckdb`).
- Tables are exported to `silver/*.parquet`.
- All transformations are deterministic SQL over Step 1 Bronze outputs.
