# Design Decisions

Generated: 2026-03-17 (America/New_York)

## Step 3 Decisions

1. Keep Gold marts strictly downstream of canonical facts/dimensions.
2. Use a transparent weighted composite score with exposed components.
3. Separate linkage QA (`gold_linkage_quality`) from reliability marts.
4. Keep GTFS-RT live pipeline isolated in a side-car Airflow DAG.
5. Defer spatial hotspot analytics behind confidence gating.

## Why This Shape

- Preserves auditability from Raw/Bronze/Silver to stakeholder marts.
- Enables clear debugging of score shifts through component visibility.
- Prevents live-alert operational complexity from contaminating batch marts.
- Supports incremental maturity: scaffold now, promote features after confidence gates pass.

## Tradeoffs

- Deterministic scoring is simple but may over-rank sparse segments.
- GTFS-RT validation quality is currently constrained by snapshot availability.
- Spatial hotspot remains intentionally incomplete until linkage confidence improves.
