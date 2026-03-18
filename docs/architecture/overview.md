# Overview

Generated: 2026-03-17 (America/New_York)

TTC Pulse (TTC Reliability Observatory) is an MVP analytics system for transit delay reliability, linkage QA, and alert validation.

## Architecture Summary

- **Raw:** immutable source registries.
- **Bronze:** row-preserving ingestion + lineage.
- **Silver/Facts:** canonical normalization and linkage metadata.
- **Gold:** stakeholder marts for rankings, reliability, and validation.
- **Dashboard:** Streamlit multipage app in locked panel order.
- **Scheduler:** one side-car Airflow DAG for GTFS-RT service alerts only.

## Core Scope

- Historical bus delay logs
- Historical subway delay logs
- Static GTFS
- GTFS-RT service alerts (alerts only)

Streetcar, trip updates, and vehicle positions remain out of MVP core scope.
