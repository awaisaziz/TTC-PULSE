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

SILVER_PARQUET = ROOT_DIR / "silver" / "silver_gtfsrt_alert_entities.parquet"
TABLE_NAME = "silver_gtfsrt_alert_entities"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE silver_gtfsrt_alert_entities AS
            SELECT
                coalesce(nullif(trim(alert_id), ''), md5(coalesce(lineage_source_file, '') || ':' || coalesce(cast(lineage_source_row_number as varchar), '0'))) AS alert_entity_id,
                nullif(trim(alert_id), '') AS alert_id,
                try_cast(active_period_start_utc as timestamp) AS active_period_start_ts,
                try_cast(active_period_end_utc as timestamp) AS active_period_end_ts,
                nullif(trim(cause), '') AS cause,
                nullif(trim(effect), '') AS effect,
                nullif(trim(severity_level), '') AS severity_level,
                nullif(trim(header_text), '') AS header_text,
                nullif(trim(description_text), '') AS description_text,
                nullif(trim(url), '') AS url,
                nullif(trim(informed_entity_route_id), '') AS informed_entity_route_id,
                nullif(trim(informed_entity_stop_id), '') AS informed_entity_stop_id,
                nullif(trim(informed_entity_trip_id), '') AS informed_entity_trip_id,
                nullif(trim(snapshot_id), '') AS snapshot_id,
                try_cast(snapshot_timestamp_utc as timestamp) AS snapshot_timestamp_ts,
                entity_index,
                CASE
                    WHEN coalesce(nullif(trim(informed_entity_route_id), ''), nullif(trim(informed_entity_stop_id), ''), nullif(trim(informed_entity_trip_id), '')) IS NOT NULL THEN 'gtfs_entity_exact'
                    ELSE 'none'
                END AS match_method,
                CASE
                    WHEN coalesce(nullif(trim(informed_entity_route_id), ''), nullif(trim(informed_entity_stop_id), ''), nullif(trim(informed_entity_trip_id), '')) IS NOT NULL THEN 0.95
                    ELSE 0.00
                END AS match_confidence,
                CASE
                    WHEN coalesce(nullif(trim(informed_entity_route_id), ''), nullif(trim(informed_entity_stop_id), ''), nullif(trim(informed_entity_trip_id), '')) IS NOT NULL THEN 'LINKABLE'
                    ELSE 'UNLINKED'
                END AS link_status,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM bronze_gtfsrt_alert_entities;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, SILVER_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)
    append_ingestion_log(
        step="normalize_gtfsrt_entities",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(SILVER_PARQUET),
        details="GTFS-RT alert entities normalized for silver canonical schema.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
