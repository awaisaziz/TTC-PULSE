from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.utils.project_setup import (
    BRONZE_DIR,
    DATA_DIR,
    append_ingestion_log,
    connect_duckdb,
    copy_table_to_parquet,
    discover_csv_files,
    ensure_duckdb_database,
    ensure_project_structure,
    fetch_table_count,
    read_registry_paths,
    sanitize_identifier,
    sql_quote,
    sql_string_list,
    table_exists,
    to_rel_posix,
    write_source_inventory_doc,
    write_step1_summary_doc,
)


def create_bronze_from_csv_files(
    conn,
    table_name: str,
    source_registry_table: str,
    csv_files: list[Path],
) -> int:
    if not csv_files:
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} (
                lineage_source_file VARCHAR,
                lineage_source_row_number BIGINT,
                lineage_bronze_loaded_at_utc VARCHAR,
                lineage_source_registry VARCHAR
            );
            """
        )
        return 0

    csv_sql_list = sql_string_list(csv_files)
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT
            src.*,
            src.filename AS lineage_source_file,
            row_number() OVER (PARTITION BY src.filename ORDER BY src.filename) AS lineage_source_row_number,
            strftime(now(), '%Y-%m-%dT%H:%M:%SZ') AS lineage_bronze_loaded_at_utc,
            {sql_quote(source_registry_table)} AS lineage_source_registry
        FROM read_csv_auto(
            {csv_sql_list},
            header=true,
            all_varchar=true,
            union_by_name=true,
            filename=true,
            ignore_errors=true,
            sample_size=-1
        ) AS src;
        """
    )
    return fetch_table_count(conn, table_name)


def create_bronze_gtfsrt_shell(conn) -> int:
    conn.execute(
        """
        CREATE OR REPLACE TABLE bronze_gtfsrt_alert_entities (
            alert_id VARCHAR,
            active_period_start_utc VARCHAR,
            active_period_end_utc VARCHAR,
            cause VARCHAR,
            effect VARCHAR,
            severity_level VARCHAR,
            header_text VARCHAR,
            description_text VARCHAR,
            url VARCHAR,
            informed_entity_route_id VARCHAR,
            informed_entity_stop_id VARCHAR,
            informed_entity_trip_id VARCHAR,
            snapshot_id VARCHAR,
            snapshot_timestamp_utc VARCHAR,
            entity_index BIGINT,
            lineage_source_file VARCHAR,
            lineage_source_row_number BIGINT,
            lineage_bronze_loaded_at_utc VARCHAR,
            lineage_source_registry VARCHAR
        );
        """
    )
    return 0


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()

    with connect_duckdb() as conn:
        if table_exists(conn, "raw_bus_delay_events_registry"):
            bus_files = read_registry_paths(conn, "raw_bus_delay_events_registry")
        else:
            bus_files = discover_csv_files(
                DATA_DIR / "bus",
                include_any=("ttc-bus-delay-data", "ttc bus delay data"),
                exclude_any=("code description", "readme"),
            )

        if table_exists(conn, "raw_subway_delay_events_registry"):
            subway_files = read_registry_paths(conn, "raw_subway_delay_events_registry")
        else:
            subway_files = discover_csv_files(
                DATA_DIR / "subway",
                include_any=("ttc-subway-delay", "subway delay data"),
                exclude_any=("code description", "delay-codes", "readme", "meta_data", "meta data"),
            )

        if table_exists(conn, "raw_gtfs_static_files_registry"):
            gtfs_files = read_registry_paths(conn, "raw_gtfs_static_files_registry")
        else:
            gtfs_files = discover_csv_files(DATA_DIR / "gtfs")

        bus_count = create_bronze_from_csv_files(
            conn=conn,
            table_name="bronze_bus_events",
            source_registry_table="raw_bus_delay_events_registry",
            csv_files=bus_files,
        )
        copy_table_to_parquet(conn, "bronze_bus_events", BRONZE_DIR / "bronze_bus_events.parquet")
        append_ingestion_log(
            step="build_bronze_bus",
            status="SUCCESS",
            row_count=bus_count,
            output_path=to_rel_posix(BRONZE_DIR / "bronze_bus_events.parquet"),
            details=f"source_files={len(bus_files)}",
        )

        subway_count = create_bronze_from_csv_files(
            conn=conn,
            table_name="bronze_subway_events",
            source_registry_table="raw_subway_delay_events_registry",
            csv_files=subway_files,
        )
        copy_table_to_parquet(conn, "bronze_subway_events", BRONZE_DIR / "bronze_subway_events.parquet")
        append_ingestion_log(
            step="build_bronze_subway",
            status="SUCCESS",
            row_count=subway_count,
            output_path=to_rel_posix(BRONZE_DIR / "bronze_subway_events.parquet"),
            details=f"source_files={len(subway_files)}",
        )

        gtfs_table_count = 0
        for gtfs_file in gtfs_files:
            table_name = f"bronze_gtfs_{sanitize_identifier(gtfs_file.stem)}"
            gtfs_rows = create_bronze_from_csv_files(
                conn=conn,
                table_name=table_name,
                source_registry_table="raw_gtfs_static_files_registry",
                csv_files=[gtfs_file],
            )
            copy_table_to_parquet(conn, table_name, BRONZE_DIR / f"{table_name}.parquet")
            append_ingestion_log(
                step=f"build_{table_name}",
                status="SUCCESS",
                row_count=gtfs_rows,
                output_path=to_rel_posix(BRONZE_DIR / f"{table_name}.parquet"),
                details=f"source_file={gtfs_file.name}",
            )
            gtfs_table_count += 1

        gtfsrt_count = create_bronze_gtfsrt_shell(conn)
        copy_table_to_parquet(
            conn,
            "bronze_gtfsrt_alert_entities",
            BRONZE_DIR / "bronze_gtfsrt_alert_entities.parquet",
        )
        append_ingestion_log(
            step="build_bronze_gtfsrt_alert_entities",
            status="SUCCESS",
            row_count=gtfsrt_count,
            output_path=to_rel_posix(BRONZE_DIR / "bronze_gtfsrt_alert_entities.parquet"),
            details="schema_ready_shell_only",
        )

        write_source_inventory_doc(conn)
        write_step1_summary_doc(conn)

    print(
        "Bronze build complete: "
        f"bus={bus_count}, subway={subway_count}, gtfs_tables={gtfs_table_count}, gtfsrt_shell={gtfsrt_count}"
    )


if __name__ == "__main__":
    main()
