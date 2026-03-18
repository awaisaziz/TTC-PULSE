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

TABLE_NAME = "gold_alert_validation"
PARQUET_PATH = ROOT_DIR / "gold" / "gold_alert_validation.parquet"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()

    with connect_duckdb() as conn:
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {TABLE_NAME} AS
            WITH alerts AS (
                SELECT
                    alert_entity_id,
                    alert_id,
                    coalesce(active_period_start_ts, snapshot_timestamp_ts) AS alert_start_ts,
                    coalesce(active_period_end_ts, snapshot_timestamp_ts + INTERVAL '30 minutes') AS alert_end_ts,
                    snapshot_timestamp_ts,
                    matched_route_id,
                    matched_stop_id,
                    cause,
                    effect,
                    severity_level,
                    match_method,
                    match_confidence,
                    link_status
                FROM fact_gtfsrt_alerts_norm
            ),
            alert_rows AS (
                SELECT
                    a.alert_entity_id,
                    a.alert_id,
                    a.alert_start_ts,
                    a.alert_end_ts,
                    a.snapshot_timestamp_ts,
                    a.matched_route_id,
                    a.matched_stop_id,
                    a.cause,
                    a.effect,
                    a.severity_level,
                    a.match_method,
                    a.match_confidence,
                    a.link_status,
                    count(d.event_id) AS matched_delay_events,
                    avg(d.delay_minutes) AS avg_delay_minutes,
                    quantile_cont(d.delay_minutes, 0.9) AS p90_delay_minutes,
                    CASE
                        WHEN count(d.event_id) > 0 THEN 'VALIDATED_BY_DELAY_EVENTS'
                        WHEN a.link_status = 'UNLINKED' THEN 'UNLINKED_ALERT'
                        ELSE 'NO_DELAY_EVIDENCE'
                    END AS validation_status
                FROM alerts a
                LEFT JOIN fact_delay_events_norm d
                  ON (
                       (a.matched_route_id IS NOT NULL AND d.matched_route_id = a.matched_route_id)
                    OR (a.matched_stop_id IS NOT NULL AND d.matched_stop_id = a.matched_stop_id)
                  )
                 AND d.event_ts BETWEEN (a.alert_start_ts - INTERVAL '30 minutes')
                                   AND (a.alert_end_ts + INTERVAL '30 minutes')
                GROUP BY
                    a.alert_entity_id,
                    a.alert_id,
                    a.alert_start_ts,
                    a.alert_end_ts,
                    a.snapshot_timestamp_ts,
                    a.matched_route_id,
                    a.matched_stop_id,
                    a.cause,
                    a.effect,
                    a.severity_level,
                    a.match_method,
                    a.match_confidence,
                    a.link_status
            ),
            snapshot_entities AS (
                SELECT
                    snapshot_id,
                    count(*) AS parsed_entity_count
                FROM silver_gtfsrt_alert_entities
                GROUP BY snapshot_id
            ),
            snapshot_health AS (
                SELECT
                    md5('snapshot:' || coalesce(regexp_replace(r.source_file_name, '\\.[^.]+$', ''), 'unknown')) AS alert_entity_id,
                    NULL::VARCHAR AS alert_id,
                    NULL::TIMESTAMP AS alert_start_ts,
                    NULL::TIMESTAMP AS alert_end_ts,
                    try_cast(r.discovered_utc as timestamp) AS snapshot_timestamp_ts,
                    NULL::VARCHAR AS matched_route_id,
                    NULL::VARCHAR AS matched_stop_id,
                    NULL::VARCHAR AS cause,
                    NULL::VARCHAR AS effect,
                    NULL::VARCHAR AS severity_level,
                    'snapshot_health'::VARCHAR AS match_method,
                    CASE WHEN coalesce(se.parsed_entity_count, 0) > 0 THEN 0.50 ELSE 0.00 END AS match_confidence,
                    CASE WHEN coalesce(se.parsed_entity_count, 0) > 0 THEN 'LINKABLE' ELSE 'UNLINKED' END AS link_status,
                    0::BIGINT AS matched_delay_events,
                    NULL::DOUBLE AS avg_delay_minutes,
                    NULL::DOUBLE AS p90_delay_minutes,
                    CASE
                        WHEN coalesce(se.parsed_entity_count, 0) > 0 THEN 'SNAPSHOT_WITH_PARSED_ALERTS'
                        ELSE 'SNAPSHOT_WITH_NO_PARSED_ALERTS'
                    END AS validation_status
                FROM raw_gtfsrt_alert_snapshots_registry r
                LEFT JOIN snapshot_entities se
                  ON se.snapshot_id = regexp_replace(r.source_file_name, '\\.[^.]+$', '')
            )
            SELECT
                *,
                current_timestamp AS generated_at_utc
            FROM (
                SELECT * FROM alert_rows
                UNION ALL
                SELECT * FROM snapshot_health
            )
            ORDER BY snapshot_timestamp_ts DESC NULLS LAST, validation_status;
            """
        )

        copy_table_to_parquet(conn, TABLE_NAME, PARQUET_PATH)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_gold_alert_validation",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(PARQUET_PATH),
        details="Gold alert validation mart built with snapshot health coverage.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
