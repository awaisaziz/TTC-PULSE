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

TABLE_NAME = "gold_linkage_quality"
PARQUET_PATH = ROOT_DIR / "gold" / "gold_linkage_quality.parquet"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE gold_linkage_quality AS
            WITH delay_quality AS (
                SELECT
                    'delay_events' AS dataset,
                    mode,
                    count(*) AS total_rows,
                    sum(CASE WHEN link_status = 'LINKED' THEN 1 ELSE 0 END) AS linked_rows,
                    avg(match_confidence) AS avg_match_confidence,
                    quantile_cont(match_confidence, 0.5) AS median_match_confidence,
                    sum(CASE WHEN match_confidence < 0.8 THEN 1 ELSE 0 END) AS low_conf_rows
                FROM fact_delay_events_norm
                GROUP BY 1, 2
            ),
            alert_quality AS (
                SELECT
                    'gtfsrt_alerts' AS dataset,
                    'alerts' AS mode,
                    count(*) AS total_rows,
                    sum(CASE WHEN link_status = 'LINKED' THEN 1 ELSE 0 END) AS linked_rows,
                    avg(match_confidence) AS avg_match_confidence,
                    quantile_cont(match_confidence, 0.5) AS median_match_confidence,
                    sum(CASE WHEN match_confidence < 0.8 THEN 1 ELSE 0 END) AS low_conf_rows
                FROM fact_gtfsrt_alerts_norm
            )
            SELECT
                dataset,
                mode,
                total_rows,
                linked_rows,
                total_rows - linked_rows AS unlinked_rows,
                coalesce(linked_rows::DOUBLE / nullif(total_rows, 0), 0.0) AS linked_rate,
                coalesce(unlinked_rows::DOUBLE / nullif(total_rows, 0), 0.0) AS unlinked_rate,
                coalesce(avg_match_confidence, 0.0) AS avg_match_confidence,
                coalesce(median_match_confidence, 0.0) AS median_match_confidence,
                low_conf_rows,
                current_timestamp AS generated_at_utc
            FROM (
                SELECT * FROM delay_quality
                UNION ALL
                SELECT * FROM alert_quality
            );
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, PARQUET_PATH)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_gold_linkage_quality",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(PARQUET_PATH),
        details="Gold linkage quality mart built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
