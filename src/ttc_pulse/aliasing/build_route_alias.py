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

DIM_PARQUET = ROOT_DIR / "dimensions" / "dim_route_alias.parquet"
TABLE_NAME = "dim_route_alias"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE dim_route_alias AS
            WITH alias_base AS (
                SELECT DISTINCT
                    route_raw AS route_alias_raw,
                    regexp_replace(upper(coalesce(route_raw, '')), '[^A-Z0-9]+', '', 'g') AS route_alias_key,
                    'bus' AS source_mode
                FROM silver_bus_events
                WHERE route_raw IS NOT NULL AND trim(route_raw) <> ''
                UNION
                SELECT DISTINCT
                    route_raw AS route_alias_raw,
                    regexp_replace(upper(coalesce(route_raw, '')), '[^A-Z0-9]+', '', 'g') AS route_alias_key,
                    'subway' AS source_mode
                FROM silver_subway_events
                WHERE route_raw IS NOT NULL AND trim(route_raw) <> ''
            ),
            gtfs AS (
                SELECT
                    route_id,
                    route_short_name,
                    route_long_name,
                    route_key
                FROM dim_route_gtfs
            )
            SELECT
                md5(coalesce(a.route_alias_key, '') || ':' || coalesce(a.source_mode, '')) AS route_alias_id,
                a.route_alias_raw,
                a.route_alias_key,
                a.source_mode,
                g.route_id AS matched_route_id,
                g.route_short_name,
                g.route_long_name,
                CASE
                    WHEN g.route_id IS NOT NULL THEN 'route_key_exact'
                    ELSE 'unmatched'
                END AS match_method,
                CASE
                    WHEN g.route_id IS NOT NULL THEN 0.95
                    ELSE 0.00
                END AS match_confidence,
                CASE
                    WHEN g.route_id IS NOT NULL THEN 'LINKED'
                    ELSE 'UNLINKED'
                END AS link_status,
                current_timestamp AS generated_at_utc
            FROM alias_base a
            LEFT JOIN gtfs g ON g.route_key = a.route_alias_key;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, DIM_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_route_alias",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(DIM_PARQUET),
        details="Route aliases with match metadata built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
