# Gold Layer

Generated: 2026-03-17 (America/New_York)

## Purpose

Gold provides stakeholder-facing marts for reliability, linkage quality, rankings, and GTFS-RT validation.

## Implemented Gold Tables

| Table | Rows | Purpose |
|---|---:|---|
| `gold_delay_events_core` | 1026993 | Canonical event-level analytical base |
| `gold_linkage_quality` | 3 | Linkage QA summary by dataset/mode |
| `gold_route_time_metrics` | 35882 | Route x weekday x hour reliability metrics |
| `gold_station_time_metrics` | 224282 | Station x weekday x hour reliability metrics |
| `gold_time_reliability` | 337 | Time-sliced reliability overview |
| `gold_top_offender_ranking` | 100618 | Ranked route/station offenders |
| `gold_alert_validation` | 0 | GTFS-RT alert-to-delay validation |
| `gold_spatial_hotspot` | 1077 | Confidence-gated spatial hotspot candidates |

## Reliability Components

- Frequency: `freq_events`
- Severity: `sev90_delay`
- Regularity: `reg90_gap`
- Cause mix: `cause_mix`

Composite score:
- `S(u,t) = w1*z(Freq) + w2*z(Sev90) + w3*z(Reg90) + w4*CauseMix`
- Weights: `w1=0.35`, `w2=0.30`, `w3=0.20`, `w4=0.15`

## Persistence Contract

- Gold tables are registered in DuckDB (`data/ttc_pulse.duckdb`).
- Gold tables are exported to `gold/*.parquet`.
- Spatial hotspot is now materialized with confidence gating and is suitable for controlled map display.

