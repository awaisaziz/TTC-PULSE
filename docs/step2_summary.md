# Step 2 Summary

Generated: 2026-03-17 (America/New_York)

Step 2 completed: Silver canonical model, canonical facts, GTFS dimensions, bridge, alias dimensions, and review tables.

## Built Tables

| Table | Rows |
|---|---:|
| `silver_bus_events` | 776435 |
| `silver_subway_events` | 250558 |
| `silver_gtfsrt_alert_entities` | 0 |
| `fact_delay_events_norm` | 1026993 |
| `fact_gtfsrt_alerts_norm` | 0 |
| `dim_route_gtfs` | 229 |
| `dim_stop_gtfs` | 9417 |
| `dim_service_gtfs` | 8 |
| `dim_route_alias` | 1306 |
| `dim_station_alias` | 136273 |
| `dim_incident_code` | 280 |
| `bridge_route_direction_stop` | 17824 |
| `route_alias_review` | 1056 |
| `station_alias_review` | 135276 |
| `incident_code_review` | 280 |

## Output Locations

- `silver/*.parquet`
- `dimensions/*.parquet`
- `bridge/*.parquet`
- `reviews/*.parquet`
- DuckDB registrations in `data/ttc_pulse.duckdb`

## Scope Confirmation

- Bus modeled route-first.
- Subway modeled station-first after canonicalization.
- GTFS used as reference + bridge family.
- `match_method`, `match_confidence`, and `link_status` persisted.
- Silver/Fact/Dimensions/Bridge/Review only; no Gold or dashboard work in this step.
