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

SILVER_PARQUET = ROOT_DIR / "silver" / "silver_subway_events.parquet"
TABLE_NAME = "silver_subway_events"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE silver_subway_events AS
            WITH base AS (
                SELECT
                    md5(coalesce(lineage_source_file, '') || ':' || coalesce(cast(lineage_source_row_number as varchar), '0')) AS event_id,
                    coalesce(nullif(trim(Station), ''), nullif(trim(Line), '')) AS station_raw,
                    nullif(trim(Line), '') AS line_raw,
                    nullif(trim(Bound), '') AS direction_raw,
                    nullif(trim(Code), '') AS incident_code_raw,
                    NULL::VARCHAR AS incident_text_raw,
                    try_cast("Min Delay" as integer) AS delay_raw,
                    try_cast("Min Gap" as integer) AS gap_raw,
                    coalesce(
                        try_strptime("Date" || ' ' || "Time", '%Y-%m-%d %H:%M:%S'),
                        try_strptime("Date" || ' ' || "Time", '%Y-%m-%d %H:%M'),
                        try_strptime("Date" || ' ' || "Time", '%m/%d/%Y %H:%M:%S'),
                        try_strptime("Date" || ' ' || "Time", '%m/%d/%Y %H:%M'),
                        try_strptime("Date", '%Y-%m-%d'),
                        try_strptime("Date", '%m/%d/%Y')
                    ) AS event_ts,
                    filename,
                    lineage_source_file,
                    lineage_source_row_number,
                    lineage_bronze_loaded_at_utc,
                    lineage_source_registry
                FROM bronze_subway_events
            )
            SELECT
                event_id,
                'subway' AS mode,
                event_ts,
                cast(event_ts as date) AS event_date,
                line_raw AS route_raw,
                regexp_replace(upper(coalesce(line_raw, '')), '[^A-Z0-9]+', '', 'g') AS route_key,
                direction_raw,
                station_raw,
                regexp_replace(upper(coalesce(station_raw, '')), '[^A-Z0-9]+', '', 'g') AS station_key,
                incident_code_raw,
                incident_text_raw,
                coalesce(delay_raw, 0) AS delay_minutes,
                coalesce(gap_raw, 0) AS gap_minutes,
                CASE
                    WHEN station_raw IS NOT NULL AND trim(station_raw) <> '' THEN 'station_raw_exact'
                    ELSE 'none'
                END AS match_method,
                CASE
                    WHEN station_raw IS NOT NULL AND trim(station_raw) <> '' THEN 0.72
                    ELSE 0.00
                END AS match_confidence,
                CASE
                    WHEN station_raw IS NOT NULL AND trim(station_raw) <> '' THEN 'LINKABLE'
                    ELSE 'UNLINKED'
                END AS link_status,
                filename,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM base;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, SILVER_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)
    append_ingestion_log(
        step="normalize_subway",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(SILVER_PARQUET),
        details="Subway normalized to silver canonical model (station-first).",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
