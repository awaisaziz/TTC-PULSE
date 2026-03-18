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

BRIDGE_PARQUET = ROOT_DIR / "bridge" / "bridge_route_direction_stop.parquet"
TABLE_NAME = "bridge_route_direction_stop"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    with connect_duckdb() as conn:
        conn.execute(
            """
            CREATE OR REPLACE TABLE bridge_route_direction_stop AS
            WITH joined AS (
                SELECT
                    t.route_id,
                    t.direction_id,
                    st.stop_id,
                    s.stop_name,
                    min(try_cast(st.stop_sequence as integer)) AS first_stop_sequence,
                    max(try_cast(st.stop_sequence as integer)) AS last_stop_sequence,
                    count(*) AS observations,
                    min(t.lineage_source_file) AS lineage_source_file,
                    min(t.lineage_source_row_number) AS lineage_source_row_number,
                    min(t.lineage_bronze_loaded_at_utc) AS lineage_bronze_loaded_at_utc,
                    min(t.lineage_source_registry) AS lineage_source_registry
                FROM bronze_gtfs_trips t
                JOIN bronze_gtfs_stop_times st ON st.trip_id = t.trip_id
                LEFT JOIN bronze_gtfs_stops s ON s.stop_id = st.stop_id
                GROUP BY t.route_id, t.direction_id, st.stop_id, s.stop_name
            )
            SELECT
                route_id,
                direction_id,
                stop_id,
                stop_name,
                regexp_replace(upper(coalesce(stop_name, '')), '[^A-Z0-9]+', '', 'g') AS station_key,
                first_stop_sequence,
                last_stop_sequence,
                observations,
                lineage_source_file,
                lineage_source_row_number,
                lineage_bronze_loaded_at_utc,
                lineage_source_registry
            FROM joined;
            """
        )
        copy_table_to_parquet(conn, TABLE_NAME, BRIDGE_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="build_gtfs_bridge",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(BRIDGE_PARQUET),
        details="Route-direction-stop GTFS bridge built.",
    )
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
