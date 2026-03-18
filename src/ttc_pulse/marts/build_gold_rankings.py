from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.utils.project_setup import (
    ROOT_DIR,
    append_ingestion_log,
    connect_duckdb,
    copy_table_to_parquet,
    ensure_duckdb_database,
    ensure_project_structure,
    fetch_table_count,
    to_rel_posix,
)

TABLE_NAME = "gold_top_offender_ranking"
PARQUET_PATH = ROOT_DIR / "gold" / "gold_top_offender_ranking.parquet"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE gold_top_offender_ranking AS
            WITH route_rollup AS (
                SELECT
                    'route' AS entity_type,
                    mode,
                    route_key AS entity_key,
                    sum(freq_events) AS total_events,
                    avg(sev90_delay) AS avg_sev90_delay,
                    avg(reg90_gap) AS avg_reg90_gap,
                    avg(cause_mix) AS avg_cause_mix,
                    avg(reliability_composite_score) AS reliability_composite_score
                FROM gold_route_time_metrics
                GROUP BY 1, 2, 3
            ),
            station_rollup AS (
                SELECT
                    'station' AS entity_type,
                    mode,
                    station_key AS entity_key,
                    sum(freq_events) AS total_events,
                    avg(sev90_delay) AS avg_sev90_delay,
                    avg(reg90_gap) AS avg_reg90_gap,
                    avg(cause_mix) AS avg_cause_mix,
                    avg(reliability_composite_score) AS reliability_composite_score
                FROM gold_station_time_metrics
                GROUP BY 1, 2, 3
            ),
            combined AS (
                SELECT * FROM route_rollup
                UNION ALL
                SELECT * FROM station_rollup
            )
            SELECT
                dense_rank() OVER (ORDER BY reliability_composite_score DESC, total_events DESC) AS offender_rank,
                entity_type,
                mode,
                entity_key,
                total_events,
                avg_sev90_delay,
                avg_reg90_gap,
                avg_cause_mix,
                reliability_composite_score,
                current_timestamp AS generated_at_utc
            FROM combined
            WHERE entity_key IS NOT NULL AND trim(entity_key) <> '';
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, PARQUET_PATH)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_gold_rankings",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(PARQUET_PATH),
        details="Top offender ranking mart built from route/station reliability composite scores.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
