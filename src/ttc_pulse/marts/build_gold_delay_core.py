from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.marts.scoring import W1, W2, W3, W4, composite_score_expr, z_expr
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

TABLE_NAME = "gold_delay_events_core"
PARQUET_PATH = ROOT_DIR / "gold" / "gold_delay_events_core.parquet"
SPATIAL_TABLE = "gold_spatial_hotspot"
SPATIAL_PARQUET_PATH = ROOT_DIR / "gold" / "gold_spatial_hotspot.parquet"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()

    score_expr = composite_score_expr("freq_events", "sev90_delay", "reg90_gap", "cause_mix")
    zf = z_expr("freq_events")
    zs = z_expr("sev90_delay")
    zr = z_expr("reg90_gap")

    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE gold_delay_events_core AS
            SELECT
                event_id,
                mode,
                event_ts,
                event_date,
                coalesce(dayname(event_ts), dayname(cast(event_date as timestamp))) AS weekday_name,
                coalesce(extract('hour' FROM event_ts), 0)::INTEGER AS hour_of_day,
                route_raw,
                route_key,
                direction_raw,
                station_raw,
                station_key,
                incident_code_raw,
                incident_text_raw,
                delay_minutes,
                gap_minutes,
                matched_route_id,
                matched_stop_id,
                incident_code_id,
                match_method,
                match_confidence,
                link_status,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM fact_delay_events_norm;
            """
        )

        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {SPATIAL_TABLE} AS
            WITH stop_id_ref AS (
                SELECT
                    stop_id,
                    min(stop_name) AS stop_name,
                    avg(stop_lat) AS stop_lat,
                    avg(stop_lon) AS stop_lon
                FROM dim_stop_gtfs
                GROUP BY stop_id
            ),
            station_ref AS (
                SELECT
                    station_key,
                    min(stop_id) AS fallback_stop_id
                FROM dim_stop_gtfs
                WHERE station_key IS NOT NULL AND trim(station_key) <> ''
                GROUP BY station_key
            ),
            resolved AS (
                SELECT
                    d.mode,
                    d.station_key,
                    d.route_key,
                    d.incident_code_raw,
                    d.delay_minutes,
                    d.gap_minutes,
                    d.match_confidence,
                    coalesce(d.matched_stop_id, sr.fallback_stop_id) AS resolved_stop_id
                FROM gold_delay_events_core d
                LEFT JOIN station_ref sr
                    ON d.matched_stop_id IS NULL
                   AND d.station_key = sr.station_key
            ),
            joined AS (
                SELECT
                    r.*,
                    s.stop_name,
                    s.stop_lat,
                    s.stop_lon
                FROM resolved r
                LEFT JOIN stop_id_ref s ON s.stop_id = r.resolved_stop_id
            ),
            agg AS (
                SELECT
                    mode,
                    resolved_stop_id AS stop_id,
                    coalesce(station_key, 'UNKNOWN') AS station_key,
                    coalesce(route_key, 'UNKNOWN') AS route_key,
                    min(stop_name) AS stop_name,
                    avg(stop_lat) AS stop_lat,
                    avg(stop_lon) AS stop_lon,
                    count(*) AS freq_events,
                    quantile_cont(delay_minutes, 0.9) AS sev90_delay,
                    quantile_cont(gap_minutes, 0.9) AS reg90_gap,
                    coalesce(count(DISTINCT incident_code_raw)::DOUBLE / nullif(count(*), 0), 0.0) AS cause_mix,
                    avg(match_confidence) AS avg_match_confidence
                FROM joined
                WHERE resolved_stop_id IS NOT NULL
                  AND stop_lat IS NOT NULL
                  AND stop_lon IS NOT NULL
                GROUP BY 1, 2, 3, 4
            )
            SELECT
                md5(mode || ':' || coalesce(stop_id, '') || ':' || station_key) AS hotspot_id,
                mode,
                station_key,
                route_key,
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                freq_events,
                sev90_delay,
                reg90_gap,
                cause_mix,
                avg_match_confidence,
                {zf} AS z_freq,
                {zs} AS z_sev90,
                {zr} AS z_reg90,
                {W1} AS weight_freq,
                {W2} AS weight_sev90,
                {W3} AS weight_reg90,
                {W4} AS weight_cause_mix,
                {score_expr} AS hotspot_score,
                CASE
                    WHEN freq_events >= 30 AND avg_match_confidence >= 0.75 THEN TRUE
                    ELSE FALSE
                END AS confidence_gate_passed,
                CASE
                    WHEN freq_events >= 30 AND avg_match_confidence >= 0.75 THEN 'PASSED'
                    WHEN freq_events < 30 THEN 'LOW_EVENT_VOLUME'
                    WHEN avg_match_confidence < 0.75 THEN 'LOW_LINK_CONFIDENCE'
                    ELSE 'BLOCKED'
                END AS confidence_gate_reason,
                current_timestamp AS generated_at_utc
            FROM agg
            ORDER BY hotspot_score DESC;
            """
        )

        copy_table_to_parquet(conn, TABLE_NAME, PARQUET_PATH)
        copy_table_to_parquet(conn, SPATIAL_TABLE, SPATIAL_PARQUET_PATH)
        row_count = fetch_table_count(conn, TABLE_NAME)
        spatial_count = fetch_table_count(conn, SPATIAL_TABLE)

    append_ingestion_log(
        step="build_gold_delay_core",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(PARQUET_PATH),
        details=f"Gold delay core and spatial hotspot built; spatial_rows={spatial_count}",
    )
    print(f"{TABLE_NAME}: {row_count}")
    print(f"{SPATIAL_TABLE}: {spatial_count}")


if __name__ == "__main__":
    main()
