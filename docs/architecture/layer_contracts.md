# Layer Contracts

Generated: 2026-03-17 (America/New_York)

## Raw Contract

- Immutable source registries only.
- Raw file hashes and metadata are tracked.
- Raw files are not mutated in place.

## Bronze Contract

- Row-preserving extraction from source files.
- No business-rule canonicalization.
- Mandatory lineage columns are appended.

## Silver Contract

- Canonical normalization with mode-specific modeling:
  - Bus is route-first.
  - Subway is station-first.
  - GTFS-RT entities are normalized against GTFS identifiers when available.
- Match metadata is mandatory:
  - `match_method`
  - `match_confidence`
  - `link_status`

## Dimension Contract

- `dim_route_gtfs`, `dim_stop_gtfs`, `dim_service_gtfs` provide GTFS reference entities.
- Alias dimensions (`dim_route_alias`, `dim_station_alias`) map operational labels to GTFS reference IDs.
- `dim_incident_code` canonicalizes incident code semantics and flags ambiguities.

## Bridge Contract

- `bridge_route_direction_stop` captures route-direction-stop relationships from GTFS trips + stop_times.

## Review Contract

- Review tables isolate low-confidence or unresolved mappings:
  - `route_alias_review`
  - `station_alias_review`
  - `incident_code_review`
