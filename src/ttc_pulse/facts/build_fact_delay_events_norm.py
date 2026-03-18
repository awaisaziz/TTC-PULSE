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

FACT_PARQUET = ROOT_DIR / "silver" / "fact_delay_events_norm.parquet"
TABLE_NAME = "fact_delay_events_norm"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE fact_delay_events_norm AS
            WITH route_alias_best AS (
                SELECT * EXCLUDE(rn)
                FROM (
                    SELECT
                        *,
                        row_number() OVER (
                            PARTITION BY route_alias_key, source_mode
                            ORDER BY match_confidence DESC, link_status DESC, coalesce(matched_route_id, ''), coalesce(route_alias_raw, '')
                        ) AS rn
                    FROM dim_route_alias
                )
                WHERE rn = 1
            ),
            station_alias_best AS (
                SELECT * EXCLUDE(rn)
                FROM (
                    SELECT
                        *,
                        row_number() OVER (
                            PARTITION BY station_key, source_mode
                            ORDER BY match_confidence DESC, link_status DESC, coalesce(matched_stop_id, ''), coalesce(station_alias_raw, '')
                        ) AS rn
                    FROM dim_station_alias
                )
                WHERE rn = 1
            ),
            bus_enriched AS (
                SELECT
                    b.event_id,
                    b.mode,
                    b.event_ts,
                    b.event_date,
                    b.route_raw,
                    b.route_key,
                    b.direction_raw,
                    b.location_raw AS station_raw,
                    b.station_key,
                    b.incident_code_raw,
                    b.incident_text_raw,
                    b.delay_minutes,
                    b.gap_minutes,
                    coalesce(ra.matched_route_id, NULL) AS matched_route_id,
                    coalesce(sa.matched_stop_id, NULL) AS matched_stop_id,
                    coalesce(ic.incident_code_id, NULL) AS incident_code_id,
                    coalesce(ra.match_method, b.match_method) AS match_method,
                    greatest(coalesce(ra.match_confidence, 0.0), coalesce(sa.match_confidence, 0.0), coalesce(b.match_confidence, 0.0)) AS match_confidence,
                    CASE
                        WHEN ra.link_status = 'LINKED' OR sa.link_status = 'LINKED' THEN 'LINKED'
                        ELSE b.link_status
                    END AS link_status,
                    b.lineage_source_file,
                    b.lineage_source_row_number,
                    b.lineage_bronze_loaded_at_utc,
                    b.lineage_source_registry
                FROM silver_bus_events b
                LEFT JOIN route_alias_best ra
                    ON ra.route_alias_key = b.route_key
                   AND ra.source_mode = 'bus'
                LEFT JOIN station_alias_best sa
                    ON sa.station_key = b.station_key
                   AND sa.source_mode = 'bus'
                LEFT JOIN dim_incident_code ic
                    ON ic.source_mode = 'bus'
                   AND ic.incident_code = b.incident_code_raw
            ),
            subway_enriched AS (
                SELECT
                    s.event_id,
                    s.mode,
                    s.event_ts,
                    s.event_date,
                    s.route_raw,
                    s.route_key,
                    s.direction_raw,
                    s.station_raw,
                    s.station_key,
                    s.incident_code_raw,
                    s.incident_text_raw,
                    s.delay_minutes,
                    s.gap_minutes,
                    coalesce(ra.matched_route_id, NULL) AS matched_route_id,
                    coalesce(sa.matched_stop_id, NULL) AS matched_stop_id,
                    coalesce(ic.incident_code_id, NULL) AS incident_code_id,
                    coalesce(sa.match_method, s.match_method) AS match_method,
                    greatest(coalesce(ra.match_confidence, 0.0), coalesce(sa.match_confidence, 0.0), coalesce(s.match_confidence, 0.0)) AS match_confidence,
                    CASE
                        WHEN ra.link_status = 'LINKED' OR sa.link_status = 'LINKED' THEN 'LINKED'
                        ELSE s.link_status
                    END AS link_status,
                    s.lineage_source_file,
                    s.lineage_source_row_number,
                    s.lineage_bronze_loaded_at_utc,
                    s.lineage_source_registry
                FROM silver_subway_events s
                LEFT JOIN route_alias_best ra
                    ON ra.route_alias_key = s.route_key
                   AND ra.source_mode = 'subway'
                LEFT JOIN station_alias_best sa
                    ON sa.station_key = s.station_key
                   AND sa.source_mode = 'subway'
                LEFT JOIN dim_incident_code ic
                    ON ic.source_mode = 'subway'
                   AND ic.incident_code = s.incident_code_raw
            )
            SELECT * FROM bus_enriched
            UNION ALL
            SELECT * FROM subway_enriched;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, FACT_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_fact_delay_events_norm",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(FACT_PARQUET),
        details="Unified delay fact for bus (route-first) and subway (station-first).",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
