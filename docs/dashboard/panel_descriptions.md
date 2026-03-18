# Panel Descriptions

Generated: 2026-03-17 (America/New_York)

Dashboard panel order is fixed for the MVP rollout:

1. **Linkage QA panel**
   - Uses `gold_linkage_quality` and review queue counts.
   - Purpose: expose linked/unlinked rates and QA backlog.
2. **Reliability overview**
   - Uses `gold_time_reliability`.
   - Purpose: high-level reliability trends and score distribution context.
3. **Bus route ranking**
   - Uses `gold_top_offender_ranking` filtered to `entity_type=route`, `mode=bus`.
4. **Subway station ranking**
   - Uses `gold_top_offender_ranking` filtered to `entity_type=station`, `mode=subway`.
5. **Weekday x hour heatmap**
   - Uses `gold_time_reliability`.
   - Purpose: detect time-of-week reliability hotspots.
6. **Monthly trends**
   - Uses monthly rollups from `gold_delay_events_core`.
7. **Cause/category mix**
   - Uses incident mix from `gold_delay_events_core`.
8. **Live alert validation panel**
   - Uses `gold_alert_validation`.
   - Purpose: compare alert feed activity against delay evidence.
9. **Spatial hotspot map (confidence-gated)**
   - Uses `gold_spatial_hotspot` with `confidence_gate_passed` and `confidence_gate_reason`.
   - Purpose: visualize geospatial TTC hotspot candidates while preserving quality controls.

