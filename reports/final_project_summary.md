# Final Project Summary

Generated: 2026-03-17 (America/New_York)

## Project

TTC Pulse / TTC Reliability Observatory MVP

## Delivered Scope

- Step 1: Raw + Bronze + DuckDB foundation.
- Step 2: Silver canonical model, facts, dimensions, bridge, review QA tables.
- Step 3: Gold stakeholder marts, reliability scoring framework, GTFS-RT side-car DAG.
- Step 4: Streamlit dashboard, deployment package, final technical and delivery documentation.

## Dashboard Panels (Locked Order)

1. Linkage QA panel
2. Reliability overview
3. Bus route ranking
4. Subway station ranking
5. Weekday x hour heatmap
6. Monthly trends
7. Cause/category mix
8. Live alert validation panel
9. Spatial hotspot map later (placeholder)

## Runtime Target

- Streamlit deployment
- DuckDB + Parquet backend
- Spark excluded from MVP

## Final Notes

- Gold marts and dashboard are locally runnable.
- Live alert chain is operationally scaffolded and scheduler-ready.
- Spatial hotspot remains deferred pending confidence-gating criteria.
