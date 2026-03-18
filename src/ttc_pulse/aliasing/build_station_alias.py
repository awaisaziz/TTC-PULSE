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

DIM_PARQUET = ROOT_DIR / "dimensions" / "dim_station_alias.parquet"
TABLE_NAME = "dim_station_alias"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_station_alias AS
            WITH station_base AS (
                SELECT DISTINCT
                    station_raw AS station_alias_raw,
                    regexp_replace(upper(coalesce(station_raw, '')), '[^A-Z0-9]+', '', 'g') AS station_key,
                    'subway' AS source_mode
                FROM silver_subway_events
                WHERE station_raw IS NOT NULL AND trim(station_raw) <> ''
                UNION
                SELECT DISTINCT
                    location_raw AS station_alias_raw,
                    regexp_replace(upper(coalesce(location_raw, '')), '[^A-Z0-9]+', '', 'g') AS station_key,
                    'bus' AS source_mode
                FROM silver_bus_events
                WHERE location_raw IS NOT NULL AND trim(location_raw) <> ''
            ),
            gtfs_exact AS (
                SELECT
                    stop_id,
                    stop_name,
                    station_key
                FROM dim_stop_gtfs
            )
            SELECT
                md5(coalesce(s.station_key, '') || ':' || coalesce(s.source_mode, '')) AS station_alias_id,
                s.station_alias_raw,
                s.station_key,
                s.source_mode,
                g.stop_id AS matched_stop_id,
                g.stop_name AS matched_stop_name,
                CASE
                    WHEN g.stop_id IS NOT NULL THEN 'station_key_exact'
                    ELSE 'unmatched'
                END AS match_method,
                CASE
                    WHEN g.stop_id IS NOT NULL THEN 0.85
                    ELSE 0.00
                END AS match_confidence,
                CASE
                    WHEN g.stop_id IS NOT NULL THEN 'LINKED'
                    ELSE 'UNLINKED'
                END AS link_status,
                current_timestamp AS generated_at_utc
            FROM station_base s
            LEFT JOIN gtfs_exact g ON g.station_key = s.station_key;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, DIM_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_station_alias",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(DIM_PARQUET),
        details="Station aliases with match metadata built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
