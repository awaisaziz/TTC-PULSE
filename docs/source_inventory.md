# Source Inventory

Generated (UTC): 2026-03-17T20:01:13Z

Streetcar datasets are intentionally excluded from the core MVP source inventory.

## Raw Registries

| Source | Registry Table | Files Registered |
|---|---|---:|
| Historical TTC bus delay logs | `raw_bus_delay_events_registry` | 100 |
| Historical TTC subway delay logs | `raw_subway_delay_events_registry` | 61 |
| Static GTFS files | `raw_gtfs_static_files_registry` | 8 |
| GTFS-RT alert snapshots | `raw_gtfsrt_alert_snapshots_registry` | 0 |

## Bronze Tables

| Bronze Table | Rows |
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
