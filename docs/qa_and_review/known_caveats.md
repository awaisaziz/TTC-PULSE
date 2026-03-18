# Known Caveats

Generated: 2026-03-17 (America/New_York)

## Data Quality Caveats

- Operational station/location text is highly variable; deterministic key matching leaves many unresolved station aliases.
- Incident descriptions are sparse in subway records; many codes remain review candidates.
- GTFS-RT alerts are currently empty because polling snapshots are deferred in MVP setup.

## Modeling Caveats

- Alias matching currently uses deterministic exact-key logic only.
- No fuzzy lexical/phonetic matching or curated override dictionary is applied in Step 2.
- `match_confidence` is heuristic and should be recalibrated once manual validation feedback is available.

## Scope Caveats

- Streetcar remains excluded from core MVP model.
- Silver/Fact outputs are finalized for Step 2 only; Gold marts/dashboard logic is intentionally deferred.
