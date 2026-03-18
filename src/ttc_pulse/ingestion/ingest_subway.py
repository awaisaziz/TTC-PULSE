from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.utils.project_setup import (
    DATA_DIR,
    RAW_DIR,
    append_ingestion_log,
    build_registry_records,
    connect_duckdb,
    discover_csv_files,
    ensure_duckdb_database,
    ensure_project_structure,
    to_rel_posix,
    write_registry_outputs,
)

TABLE_NAME = "raw_subway_delay_events_registry"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()

    source_files = discover_csv_files(
        DATA_DIR / "subway",
        include_any=("ttc-subway-delay", "subway delay data"),
        exclude_any=("code description", "delay-codes", "readme", "meta_data", "meta data"),
    )
    records = build_registry_records(
        files=source_files,
        dataset_name="subway_delay_events",
        source_type="historical_subway_delay_logs",
    )

    csv_output = RAW_DIR / "subway" / "raw_subway_delay_events_registry.csv"
    parquet_output = RAW_DIR / "subway" / "raw_subway_delay_events_registry.parquet"

    try:
        with connect_duckdb() as conn:
            row_count = write_registry_outputs(
                conn=conn,
                table_name=TABLE_NAME,
                csv_path=csv_output,
                parquet_path=parquet_output,
                records=records,
            )
        append_ingestion_log(
            step="ingest_subway",
            status="SUCCESS",
            row_count=row_count,
            output_path=to_rel_posix(parquet_output),
            details=f"registered_files={len(source_files)}",
        )
        print(f"{TABLE_NAME}: {row_count} registry rows from {len(source_files)} files")
    except Exception as exc:  # pragma: no cover
        append_ingestion_log(
            step="ingest_subway",
            status="FAILED",
            row_count=0,
            output_path=to_rel_posix(parquet_output),
            details=str(exc),
        )
        raise


if __name__ == "__main__":
    main()
