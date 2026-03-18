# Data Dictionary

Generated: 2026-03-17 (America/New_York)

## Gold Tables

### gold_delay_events_core
- event grain: canonical delay event
- keys: `event_id`, `mode`, `event_ts`, `event_date`
- linkage fields: `matched_route_id`, `matched_stop_id`, `match_method`, `match_confidence`, `link_status`
- metrics: `delay_minutes`, `gap_minutes`

### gold_linkage_quality
- grain: dataset x mode summary
- fields: `total_rows`, `linked_rows`, `unlinked_rows`, `linked_rate`, `avg_match_confidence`

### gold_route_time_metrics
- grain: mode x route_key x weekday x hour
- reliability components: `freq_events`, `sev90_delay`, `reg90_gap`, `cause_mix`
- score fields: `z_freq`, `z_sev90`, `z_reg90`, `reliability_composite_score`

### gold_station_time_metrics
- grain: mode x station_key x weekday x hour
- same component and score fields as route metrics

### gold_time_reliability
- grain: mode x weekday x hour
- same component and score fields for overview panel

### gold_top_offender_ranking
- grain: ranked entity record
- fields: `offender_rank`, `entity_type`, `mode`, `entity_key`, `reliability_composite_score`, `total_events`

### gold_alert_validation
- grain: alert entity validation record
- fields: alert timing, matched GTFS IDs, delay evidence counts, `validation_status`

### gold_spatial_hotspot\n- grain: confidence-gated hotspot candidate by resolved stop/station\n- fields: geospatial coordinates (`stop_lat`, `stop_lon`), reliability components, `hotspot_score`, gate fields (`confidence_gate_passed`, `confidence_gate_reason`)

## Dashboard Utility Modules

- `src/ttc_pulse/dashboard/loaders.py`: DuckDB reads and panel-specific loaders
- `src/ttc_pulse/dashboard/charts.py`: reusable Altair chart builders
- `src/ttc_pulse/dashboard/formatting.py`: numeric formatting helpers

