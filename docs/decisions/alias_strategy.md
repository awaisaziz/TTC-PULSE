# Alias Strategy

Generated: 2026-03-17 (America/New_York)

## Decision

Adopt a key-based alias strategy where operational text labels are normalized into deterministic alias keys and linked to GTFS reference dimensions.

## Route Alias

- Alias source: `silver_bus_events.route_raw`, `silver_subway_events.route_raw`
- Normalized key: uppercase alphanumeric (`route_alias_key`)
- Target reference: `dim_route_gtfs.route_id`
- Primary match method: `route_key_exact`

## Station Alias

- Alias source: `silver_subway_events.station_raw`, `silver_bus_events.location_raw`
- Normalized key: uppercase alphanumeric (`station_key`)
- Target reference: `dim_stop_gtfs.stop_id`
- Primary match method: `station_key_exact`

## Confidence and Status

- `match_confidence` quantifies confidence in alias linkage.
- `link_status` marks `LINKED` vs `UNLINKED`.
- Unresolved/low-confidence rows are routed into review tables.

## Rationale

- Deterministic keying is simple, auditable, and reproducible for MVP.
- Keeps Silver/fact build stable while exposing quality gaps through review outputs.
