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

REVIEWS_DIR = ROOT_DIR / "reviews"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE route_alias_review AS
            SELECT
                route_alias_id,
                route_alias_raw,
                route_alias_key,
                source_mode,
                matched_route_id,
                route_short_name,
                route_long_name,
                match_method,
                match_confidence,
                link_status,
                CASE
                    WHEN link_status = 'UNLINKED' THEN 'MISSING_MATCH'
                    WHEN match_confidence < 0.80 THEN 'LOW_CONFIDENCE'
                    ELSE 'OK'
                END AS review_reason,
                current_timestamp AS review_generated_at_utc
            FROM dim_route_alias
            WHERE link_status = 'UNLINKED' OR match_confidence < 0.80;
            """
        )
        copy_table_to_parquet(conn, "route_alias_review", REVIEWS_DIR / "route_alias_review.parquet")
        route_review_rows = fetch_table_count(conn, "route_alias_review")

        conn.execute(
            """
            CREATE OR REPLACE TABLE station_alias_review AS
            SELECT
                station_alias_id,
                station_alias_raw,
                station_key,
                source_mode,
                matched_stop_id,
                matched_stop_name,
                match_method,
                match_confidence,
                link_status,
                CASE
                    WHEN link_status = 'UNLINKED' THEN 'MISSING_MATCH'
                    WHEN match_confidence < 0.80 THEN 'LOW_CONFIDENCE'
                    ELSE 'OK'
                END AS review_reason,
                current_timestamp AS review_generated_at_utc
            FROM dim_station_alias
            WHERE link_status = 'UNLINKED' OR match_confidence < 0.80;
            """
        )
        copy_table_to_parquet(conn, "station_alias_review", REVIEWS_DIR / "station_alias_review.parquet")
        station_review_rows = fetch_table_count(conn, "station_alias_review")

        conn.execute(
            """
            CREATE OR REPLACE TABLE incident_code_review AS
            SELECT
                incident_code_id,
                source_mode,
                incident_code,
                canonical_incident_text,
                total_occurrences,
                variant_count,
                review_status,
                CASE
                    WHEN canonical_incident_text IS NULL OR trim(canonical_incident_text) = '' THEN 'MISSING_DESCRIPTION'
                    WHEN variant_count > 1 THEN 'MULTI_DESCRIPTION'
                    ELSE 'OK'
                END AS review_reason,
                current_timestamp AS review_generated_at_utc
            FROM dim_incident_code
            WHERE review_status = 'REVIEW'
               OR canonical_incident_text IS NULL
               OR trim(canonical_incident_text) = '';
            """
        )
        copy_table_to_parquet(conn, "incident_code_review", REVIEWS_DIR / "incident_code_review.parquet")
        incident_review_rows = fetch_table_count(conn, "incident_code_review")

    append_ingestion_log(
        step="build_review_tables",
        status="SUCCESS",
        row_count=route_review_rows + station_review_rows + incident_review_rows,
        output_path=to_rel_posix(REVIEWS_DIR),
        details=(
            f"route_alias_review={route_review_rows};"
            f"station_alias_review={station_review_rows};"
            f"incident_code_review={incident_review_rows}"
        ),
    )
    print(
        "review tables: "
        f"route_alias_review={route_review_rows}, "
        f"station_alias_review={station_review_rows}, "
        f"incident_code_review={incident_review_rows}"
    )


if __name__ == "__main__":
    main()
