# UX Decisions

Generated: 2026-03-17 (America/New_York)

## Navigation

- Multipage Streamlit with numeric prefixes (`01`-`09`) to enforce locked stakeholder panel order.
- Lightweight home page provides KPI snapshot and orientation.

## Presentation Strategy

- Each page starts with a single purpose and one primary chart.
- Tables remain visible under charts for auditability and exportability.
- Empty-state messaging is explicit for sparse feeds (especially GTFS-RT alerts).

## Filtering Defaults

- Route and station rankings default to top 50 entries.
- Heatmap defaults to composite reliability score.
- Cause mix defaults to top 15 incident categories per mode.

## Reliability Transparency

- Component metrics and composite score are displayed together.
- Linkage panel appears first to frame data confidence before downstream interpretation.

## Deferred Spatial Experience

- Spatial map is enabled with confidence-gating controls so low-confidence hotspots remain visually flagged.

