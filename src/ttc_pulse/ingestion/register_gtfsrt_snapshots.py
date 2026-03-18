from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.utils.project_setup import (
    RAW_DIR,
    ROOT_DIR,
    append_ingestion_log,
    build_registry_records,
    connect_duckdb,
    discover_files,
    ensure_duckdb_database,
    ensure_project_structure,
    to_rel_posix,
    write_registry_outputs,
)

TABLE_NAME = "raw_gtfsrt_alert_snapshots_registry"


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()

    snapshots_dir = ROOT_DIR / "alerts" / "raw_snapshots"
    snapshot_files = [f for f in discover_files(snapshots_dir) if not f.name.startswith(".")]

    records = build_registry_records(
        files=snapshot_files,
        dataset_name="gtfsrt_alert_snapshots",
        source_type="gtfsrt_service_alerts",
    )

    csv_output = RAW_DIR / "gtfsrt" / "raw_gtfsrt_alert_snapshots_registry.csv"
    parquet_output = RAW_DIR / "gtfsrt" / "raw_gtfsrt_alert_snapshots_registry.parquet"

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
            step="register_gtfsrt_snapshots",
            status="SUCCESS",
            row_count=row_count,
            output_path=to_rel_posix(parquet_output),
            details=f"registered_files={len(snapshot_files)}",
        )
        print(f"{TABLE_NAME}: {row_count} registry rows from {len(snapshot_files)} snapshot files")
    except Exception as exc:  # pragma: no cover
        append_ingestion_log(
            step="register_gtfsrt_snapshots",
            status="FAILED",
            row_count=0,
            output_path=to_rel_posix(parquet_output),
            details=str(exc),
        )
        raise


if __name__ == "__main__":
    main()

