# Review Tables

Generated: 2026-03-17 (America/New_York)

## Purpose

Review tables isolate mappings that require manual QA before promoting confidence thresholds in downstream marts.

## Implemented Tables

| Table | Rows | Trigger |
|---|---:|---|
| `route_alias_review` | 1056 | Route aliases unresolved or low-confidence |
| `station_alias_review` | 135276 | Station aliases unresolved or low-confidence |
| `incident_code_review` | 280 | Missing/ambiguous incident code descriptions |

## Columns of Interest

Common review metadata:
- source alias/code key
- matched GTFS id (nullable)
- `match_method`
- `match_confidence`
- `link_status`
- `review_reason`
- `review_generated_at_utc`

## Usage

- Treat these as analyst work queues.
- Promote rows to linked status by improving alias rules or adding controlled mapping overrides in future steps.
