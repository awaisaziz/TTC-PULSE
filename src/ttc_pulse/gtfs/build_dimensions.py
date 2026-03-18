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

DIM_DIR = ROOT_DIR / "dimensions"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_route_gtfs AS
            SELECT
                route_id,
                route_short_name,
                route_long_name,
                route_desc,
                route_type,
                route_color,
                route_text_color,
                regexp_replace(upper(coalesce(route_short_name, route_id, '')), '[^A-Z0-9]+', '', 'g') AS route_key,
                CASE WHEN route_type IN ('1', '2') THEN 'subway' ELSE 'bus' END AS route_mode_hint,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM bronze_gtfs_routes;
            """
        )
        copy_table_to_parquet(conn, "dim_route_gtfs", DIM_DIR / "dim_route_gtfs.parquet")
        route_rows = fetch_table_count(conn, "dim_route_gtfs")

        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_stop_gtfs AS
            SELECT
                stop_id,
                stop_code,
                stop_name,
                stop_desc,
                try_cast(stop_lat as double) AS stop_lat,
                try_cast(stop_lon as double) AS stop_lon,
                location_type,
                parent_station,
                wheelchair_boarding,
                regexp_replace(upper(coalesce(stop_name, '')), '[^A-Z0-9]+', '', 'g') AS station_key,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM bronze_gtfs_stops;
            """
        )
        copy_table_to_parquet(conn, "dim_stop_gtfs", DIM_DIR / "dim_stop_gtfs.parquet")
        stop_rows = fetch_table_count(conn, "dim_stop_gtfs")

        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_service_gtfs AS
            WITH base AS (
                SELECT
                    service_id,
                    try_cast(start_date as integer) AS start_date_raw,
                    try_cast(end_date as integer) AS end_date_raw,
                    monday,
                    tuesday,
                    wednesday,
                    thursday,
                    friday,
                    saturday,
                    sunday,
                    lineage_source_file,
                    lineage_source_row_number,
                    lineage_bronze_loaded_at_utc,
                    lineage_source_registry
                FROM bronze_gtfs_calendar
            ),
            exceptions AS (
                SELECT
                    service_id,
                    count(*) AS exception_days
                FROM bronze_gtfs_calendar_dates
                GROUP BY service_id
            )
            SELECT
                b.service_id,
                strptime(cast(b.start_date_raw as varchar), '%Y%m%d')::DATE AS start_date,
                strptime(cast(b.end_date_raw as varchar), '%Y%m%d')::DATE AS end_date,
                b.monday,
                b.tuesday,
                b.wednesday,
                b.thursday,
                b.friday,
                b.saturday,
                b.sunday,
                coalesce(e.exception_days, 0) AS exception_days,
                b.lineage_source_file,
                b.lineage_source_row_number,
                b.lineage_bronze_loaded_at_utc,
                b.lineage_source_registry
            FROM base b
            LEFT JOIN exceptions e USING (service_id);
            """
        )
        copy_table_to_parquet(conn, "dim_service_gtfs", DIM_DIR / "dim_service_gtfs.parquet")
        service_rows = fetch_table_count(conn, "dim_service_gtfs")

    append_ingestion_log(
        step="build_gtfs_dimensions",
        status="SUCCESS",
        row_count=route_rows + stop_rows + service_rows,
        output_path=to_rel_posix(DIM_DIR),
        details=f"dim_route_gtfs={route_rows}; dim_stop_gtfs={stop_rows}; dim_service_gtfs={service_rows}",
    )
    print(f"dim_route_gtfs={route_rows}, dim_stop_gtfs={stop_rows}, dim_service_gtfs={service_rows}")


if __name__ == "__main__":
    main()
