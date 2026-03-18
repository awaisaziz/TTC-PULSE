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

DIM_PARQUET = ROOT_DIR / "dimensions" / "dim_incident_code.parquet"
TABLE_NAME = "dim_incident_code"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_incident_code AS
            WITH codes AS (
                SELECT
                    'bus' AS source_mode,
                    incident_code_raw AS incident_code,
                    incident_text_raw AS incident_text,
                    count(*) AS occurrences
                FROM silver_bus_events
                WHERE incident_code_raw IS NOT NULL AND trim(incident_code_raw) <> ''
                GROUP BY 1, 2, 3
                UNION ALL
                SELECT
                    'subway' AS source_mode,
                    incident_code_raw AS incident_code,
                    incident_text_raw AS incident_text,
                    count(*) AS occurrences
                FROM silver_subway_events
                WHERE incident_code_raw IS NOT NULL AND trim(incident_code_raw) <> ''
                GROUP BY 1, 2, 3
            ),
            ranked AS (
                SELECT
                    source_mode,
                    incident_code,
                    incident_text,
                    occurrences,
                    row_number() OVER (
                        PARTITION BY source_mode, incident_code
                        ORDER BY occurrences DESC, coalesce(incident_text, '')
                    ) AS rn,
                    count(*) OVER (PARTITION BY source_mode, incident_code) AS variant_count,
                    sum(occurrences) OVER (PARTITION BY source_mode, incident_code) AS total_occurrences
                FROM codes
            )
            SELECT
                md5(source_mode || ':' || incident_code) AS incident_code_id,
                source_mode,
                incident_code,
                incident_text AS canonical_incident_text,
                total_occurrences,
                variant_count,
                CASE WHEN variant_count > 1 THEN 'REVIEW' ELSE 'OK' END AS review_status,
                current_timestamp AS generated_at_utc
            FROM ranked
            WHERE rn = 1;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, DIM_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_incident_code_dim",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(DIM_PARQUET),
        details="Incident code dimension with dominant text mapping built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
