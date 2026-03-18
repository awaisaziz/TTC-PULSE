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

TABLE_NAME = "gold_route_time_metrics"
PARQUET_PATH = ROOT_DIR / "gold" / "gold_route_time_metrics.parquet"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    score_expr = composite_score_expr("freq_events", "sev90_delay", "reg90_gap", "cause_mix")
    zf = z_expr("freq_events")
    zs = z_expr("sev90_delay")
    zr = z_expr("reg90_gap")

    with connect_duckdb() as conn:
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {TABLE_NAME} AS
            WITH agg AS (
                SELECT
                    mode,
                    route_key,
                    coalesce(weekday_name, 'Unknown') AS weekday_name,
                    hour_of_day,
                    count(*) AS freq_events,
                    quantile_cont(delay_minutes, 0.9) AS sev90_delay,
                    quantile_cont(gap_minutes, 0.9) AS reg90_gap,
                    coalesce(count(DISTINCT incident_code_raw)::DOUBLE / nullif(count(*), 0), 0.0) AS cause_mix,
                    avg(delay_minutes) AS avg_delay,
                    avg(gap_minutes) AS avg_gap,
                    max(match_confidence) AS max_match_confidence
                FROM gold_delay_events_core
                WHERE route_key IS NOT NULL AND trim(route_key) <> ''
                GROUP BY 1, 2, 3, 4
            )
            SELECT
                mode,
                route_key,
                weekday_name,
                hour_of_day,
                freq_events,
                sev90_delay,
                reg90_gap,
                cause_mix,
                avg_delay,
                avg_gap,
                {zf} AS z_freq,
                {zs} AS z_sev90,
                {zr} AS z_reg90,
                {W1} AS weight_freq,
                {W2} AS weight_sev90,
                {W3} AS weight_reg90,
                {W4} AS weight_cause_mix,
                {score_expr} AS reliability_composite_score,
                max_match_confidence,
                current_timestamp AS generated_at_utc
            FROM agg;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, PARQUET_PATH)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_gold_route_metrics",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(PARQUET_PATH),
        details="Route x time reliability metrics with weighted composite score built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
