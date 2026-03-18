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

FACT_PARQUET = ROOT_DIR / "silver" / "fact_gtfsrt_alerts_norm.parquet"
TABLE_NAME = "fact_gtfsrt_alerts_norm"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE fact_gtfsrt_alerts_norm AS
            SELECT
                s.alert_entity_id,
                s.alert_id,
                s.active_period_start_ts,
                s.active_period_end_ts,
                s.cause,
                s.effect,
                s.severity_level,
                s.header_text,
                s.description_text,
                s.url,
                s.informed_entity_route_id,
                s.informed_entity_stop_id,
                s.informed_entity_trip_id,
                s.snapshot_id,
                s.snapshot_timestamp_ts,
                s.entity_index,
                dr.route_id AS matched_route_id,
                ds.stop_id AS matched_stop_id,
                dt.trip_id AS matched_trip_id,
                s.match_method,
                s.match_confidence,
                CASE
                    WHEN dr.route_id IS NOT NULL OR ds.stop_id IS NOT NULL OR dt.trip_id IS NOT NULL THEN 'LINKED'
                    ELSE s.link_status
                END AS link_status,
                s.lineage_source_file,
                s.lineage_source_row_number,
                s.lineage_bronze_loaded_at_utc,
                s.lineage_source_registry
            FROM silver_gtfsrt_alert_entities s
            LEFT JOIN dim_route_gtfs dr ON dr.route_id = s.informed_entity_route_id
            LEFT JOIN dim_stop_gtfs ds ON ds.stop_id = s.informed_entity_stop_id
            LEFT JOIN bronze_gtfs_trips dt ON dt.trip_id = s.informed_entity_trip_id;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, FACT_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_fact_gtfsrt_alerts_norm",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(FACT_PARQUET),
        details="Canonical GTFS-RT alert fact table built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
