# Final Metrics Summary (Step 3)

Generated: 2026-03-17 (America/New_York)

## Gold Table Counts

- `gold_delay_events_core`: 1026993
- `gold_linkage_quality`: 3
- `gold_route_time_metrics`: 35882
- `gold_station_time_metrics`: 224282
- `gold_time_reliability`: 337
- `gold_top_offender_ranking`: 100618
- `gold_alert_validation`: 0
- `gold_spatial_hotspot` (scaffold): 0

## Reliability Framework

Composite score:
- `S(u,t) = w1*z(Freq) + w2*z(Sev90) + w3*z(Reg90) + w4*CauseMix`
- Weights: `w1=0.35`, `w2=0.30`, `w3=0.20`, `w4=0.15`

Component metrics are materialized in route/station/time marts.

## Linkage Quality Snapshot

- Bus delay linked rate: `0.8206`
- Subway delay linked rate: `0.0798`
- GTFS-RT alert linked rate: `0.0000` (no alert rows)

## Example Top Offenders (by composite)

1. `station|bus|DOWNSVIEWSTN` score `31.2095`
2. `station|bus|SCARBOROUGHTOWNCENTRE` score `17.0423`
3. `station|bus|LAROSEANDSCARLETTRD` score `12.9239`
4. `station|bus|YONGEANDNORTHYORKCENTER` score `12.2429`
5. `station|bus|YONGESTANDDREWYAVE` score `10.2622`
