# Linkage Quality

Generated: 2026-03-17 (America/New_York)

## Gold Linkage Snapshot

| Dataset | Mode | Total Rows | Linked Rows | Linked Rate | Avg Match Confidence |
|---|---|---:|---:|---:|---:|
| delay_events | bus | 776435 | 637124 | 0.8206 | 0.9031 |
| delay_events | subway | 250558 | 19992 | 0.0798 | 0.7304 |
| gtfsrt_alerts | alerts | 0 | 0 | 0.0000 | 0.0000 |

## Interpretation

- Bus linkage is comparatively strong in the MVP rule set.
- Subway station linkage remains weak and should stay under QA attention.
- GTFS-RT validation is operationally wired but currently data-empty.

## Review Tables to Use

- `route_alias_review`
- `station_alias_review`
- `incident_code_review`

These tables are the primary remediation queues for improving linkage confidence and downstream Gold quality.
