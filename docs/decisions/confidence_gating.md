# Confidence Gating

Generated: 2026-03-17 (America/New_York)

## Gate Targets

- Promote advanced Gold outputs only when linkage quality is acceptable.
- Keep low-confidence analytics in scaffold state.

## Current Gates

1. Spatial hotspot gate:
   - requires stable stop/station linkage confidence and validated geo joins.
   - status: active confidence-gated output (`gold_spatial_hotspot`) with passed/blocked rows.
2. GTFS-RT validation gate:
   - requires regular non-empty alert snapshots and parse success.
   - status: pipeline enabled, current data volume is zero in facts/gold validation.

## Operating Rule

If `gold_linkage_quality.linked_rate` is weak for the target segment, keep derived outputs advisory or scaffold-only rather than stakeholder-facing.

## Next Promotion Criteria

- sustained linked rate improvement for subway station matching.
- stable alert ingestion over multiple scheduler cycles.
- bounded score volatility across adjacent time buckets.

