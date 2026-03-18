from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import duckdb

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = ROOT_DIR / "raw"
BRONZE_DIR = ROOT_DIR / "bronze"
LOGS_DIR = ROOT_DIR / "logs"
DOCS_DIR = ROOT_DIR / "docs"
DB_PATH = DATA_DIR / "ttc_pulse.duckdb"
INGESTION_LOG_PATH = LOGS_DIR / "ingestion_log.csv"

REQUIRED_DIRS = (
    ROOT_DIR / "app",
    ROOT_DIR / "app" / "pages",
    ROOT_DIR / "raw" / "bus",
    ROOT_DIR / "raw" / "subway",
    ROOT_DIR / "raw" / "gtfs",
    ROOT_DIR / "raw" / "gtfsrt",
    ROOT_DIR / "bronze",
    ROOT_DIR / "silver",
    ROOT_DIR / "dimensions",
    ROOT_DIR / "bridge",
    ROOT_DIR / "reviews",
    ROOT_DIR / "gold",
    ROOT_DIR / "alerts" / "raw_snapshots",
    ROOT_DIR / "alerts" / "parsed",
    ROOT_DIR / "airflow" / "dags",
    ROOT_DIR / "configs",
    ROOT_DIR / "docs",
    ROOT_DIR / "reports",
    ROOT_DIR / "outputs",
    ROOT_DIR / "logs",
    ROOT_DIR / "notebooks",
    ROOT_DIR / "src" / "ttc_pulse" / "ingestion",
    ROOT_DIR / "src" / "ttc_pulse" / "bronze",
    ROOT_DIR / "tests",
)

REGISTRY_COLUMNS = (
    "registry_id",
    "dataset_name",
    "source_type",
    "source_file_name",
    "source_path",
    "file_extension",
    "file_size_bytes",
    "modified_utc",
    "sha256",
    "discovered_utc",
    "is_immutable",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_rel_posix(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def ensure_project_structure() -> None:
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def ensure_duckdb_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.touch()
    try:
        conn = duckdb.connect(str(DB_PATH))
        conn.close()
    except duckdb.IOException as exc:
        message = str(exc).lower()
        if "not a valid duckdb database file" not in message:
            raise
        # Recover from an invalid placeholder file by rotating it and creating
        # a fresh DuckDB file at the expected location.
        backup_name = f"{DB_PATH.name}.invalid.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        backup_path = DB_PATH.parent / backup_name
        DB_PATH.replace(backup_path)
        conn = duckdb.connect(str(DB_PATH))
        conn.close()


def connect_duckdb() -> duckdb.DuckDBPyConnection:
    ensure_duckdb_database()
    return duckdb.connect(str(DB_PATH))


def append_ingestion_log(
    step: str,
    status: str,
    row_count: int = 0,
    output_path: str = "",
    details: str = "",
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not INGESTION_LOG_PATH.exists() or INGESTION_LOG_PATH.stat().st_size == 0
    with INGESTION_LOG_PATH.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=("run_utc", "step", "status", "row_count", "output_path", "details"),
        )
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "run_utc": utc_now_iso(),
                "step": step,
                "status": status,
                "row_count": row_count,
                "output_path": output_path,
                "details": details,
            }
        )


def discover_csv_files(
    directory: Path,
    include_any: Sequence[str] | None = None,
    exclude_any: Sequence[str] | None = None,
) -> list[Path]:
    if not directory.exists():
        return []
    include_any = tuple(token.lower() for token in (include_any or ()))
    exclude_any = tuple(token.lower() for token in (exclude_any or ()))
    results: list[Path] = []
    for file_path in sorted(directory.glob("*.csv")):
        name = file_path.name.lower()
        if include_any and not any(token in name for token in include_any):
            continue
        if exclude_any and any(token in name for token in exclude_any):
            continue
        results.append(file_path.resolve())
    return results


def discover_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted([path.resolve() for path in directory.rglob("*") if path.is_file()])


def sha256_digest(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as input_file:
        while True:
            chunk = input_file.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def build_registry_records(
    files: Iterable[Path],
    dataset_name: str,
    source_type: str,
) -> list[dict[str, str]]:
    discovered_utc = utc_now_iso()
    records: list[dict[str, str]] = []
    for file_path in files:
        file_stat = file_path.stat()
        digest = sha256_digest(file_path)
        rel_path = to_rel_posix(file_path)
        records.append(
            {
                "registry_id": f"{dataset_name}:{file_path.name}:{digest[:12]}",
                "dataset_name": dataset_name,
                "source_type": source_type,
                "source_file_name": file_path.name,
                "source_path": rel_path,
                "file_extension": file_path.suffix.lower().replace(".", ""),
                "file_size_bytes": str(file_stat.st_size),
                "modified_utc": datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "sha256": digest,
                "discovered_utc": discovered_utc,
                "is_immutable": "true",
            }
        )
    return records


def write_registry_csv(
    csv_path: Path,
    records: Sequence[dict[str, str]],
    columns: Sequence[str] = REGISTRY_COLUMNS,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(columns))
        writer.writeheader()
        for record in records:
            writer.writerow({column: record.get(column, "") for column in columns})


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def write_registry_outputs(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    csv_path: Path,
    parquet_path: Path,
    records: Sequence[dict[str, str]],
    columns: Sequence[str] = REGISTRY_COLUMNS,
) -> int:
    ordered_records = sorted(records, key=lambda row: (row.get("source_path", ""), row.get("source_file_name", "")))
    write_registry_csv(csv_path=csv_path, records=ordered_records, columns=columns)
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM read_csv_auto(
            {sql_quote(csv_path.resolve().as_posix())},
            header=true,
            all_varchar=true
        );
        """
    )
    copy_table_to_parquet(conn=conn, table_name=table_name, parquet_path=parquet_path)
    return fetch_table_count(conn=conn, table_name=table_name)


def fetch_table_count(conn: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0])


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?;
        """,
        [table_name],
    ).fetchone()
    return bool(result and result[0] > 0)


def list_tables_like(conn: duckdb.DuckDBPyConnection, table_prefix: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name LIKE ?
        ORDER BY table_name;
        """,
        [f"{table_prefix}%"],
    ).fetchall()
    return [row[0] for row in rows]


def copy_table_to_parquet(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    parquet_path: Path,
) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    if parquet_path.exists():
        parquet_path.unlink()
    conn.execute(
        f"""
        COPY {table_name}
        TO {sql_quote(parquet_path.resolve().as_posix())}
        (FORMAT PARQUET, COMPRESSION ZSTD);
        """
    )


def sanitize_identifier(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")


def sql_string_list(paths: Sequence[Path]) -> str:
    quoted = [sql_quote(path.resolve().as_posix()) for path in paths]
    return "[" + ",".join(quoted) + "]"


def read_registry_paths(conn: duckdb.DuckDBPyConnection, table_name: str) -> list[Path]:
    rows = conn.execute(f"SELECT source_path FROM {table_name} ORDER BY source_path;").fetchall()
    return [(ROOT_DIR / row[0]).resolve() for row in rows]


def write_source_inventory_doc(conn: duckdb.DuckDBPyConnection, output_path: Path | None = None) -> None:
    output_path = output_path or (DOCS_DIR / "source_inventory.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_sources = (
        ("Historical TTC bus delay logs", "raw_bus_delay_events_registry"),
        ("Historical TTC subway delay logs", "raw_subway_delay_events_registry"),
        ("Static GTFS files", "raw_gtfs_static_files_registry"),
        ("GTFS-RT alert snapshots", "raw_gtfsrt_alert_snapshots_registry"),
    )

    lines = [
        "# Source Inventory",
        "",
        f"Generated (UTC): {utc_now_iso()}",
        "",
        "Streetcar datasets are intentionally excluded from the core MVP source inventory.",
        "",
        "## Raw Registries",
        "",
        "| Source | Registry Table | Files Registered |",
        "|---|---|---:|",
    ]
    for source_name, table_name in raw_sources:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| {source_name} | `{table_name}` | {count} |")

    bronze_core = (
        "bronze_bus_events",
        "bronze_subway_events",
        "bronze_gtfsrt_alert_entities",
    )
    gtfs_tables = list_tables_like(conn, "bronze_gtfs_")
    gtfs_tables = [table for table in gtfs_tables if table != "bronze_gtfsrt_alert_entities"]

    lines.extend(
        [
            "",
            "## Bronze Tables",
            "",
            "| Bronze Table | Rows |",
            "|---|---:|",
        ]
    )
    for table_name in bronze_core:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| `{table_name}` | {count} |")
    for table_name in gtfs_tables:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| `{table_name}` | {count} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_step1_summary_doc(conn: duckdb.DuckDBPyConnection, output_path: Path | None = None) -> None:
    output_path = output_path or (DOCS_DIR / "step1_summary.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gtfs_tables = list_tables_like(conn, "bronze_gtfs_")
    gtfs_tables = [table for table in gtfs_tables if table != "bronze_gtfsrt_alert_entities"]

    lines = [
        "# Step 1 Summary",
        "",
        f"Generated (UTC): {utc_now_iso()}",
        "",
        "Step 1 scope completed: Raw + Bronze + DuckDB foundation only.",
        "",
        "## Completed",
        "",
        "- Project structure scaffolded for TTC Pulse MVP.",
        "- DuckDB database created at `data/ttc_pulse.duckdb`.",
        "- Immutable raw registries created and registered in DuckDB.",
        "- Bronze row-preserving tables with lineage columns created and exported to Parquet.",
        "- GTFS-RT Bronze entity table created as schema-ready shell (polling deferred).",
        "- Ingestion logs and source inventory generated locally.",
        "",
        "## Raw Registry Tables",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]

    raw_tables = (
        "raw_bus_delay_events_registry",
        "raw_subway_delay_events_registry",
        "raw_gtfs_static_files_registry",
        "raw_gtfsrt_alert_snapshots_registry",
    )
    for table_name in raw_tables:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| `{table_name}` | {count} |")

    lines.extend(
        [
            "",
            "## Bronze Tables",
            "",
            "| Table | Rows |",
            "|---|---:|",
        ]
    )

    bronze_tables = (
        "bronze_bus_events",
        "bronze_subway_events",
        "bronze_gtfsrt_alert_entities",
    )
    for table_name in bronze_tables:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| `{table_name}` | {count} |")

    for table_name in gtfs_tables:
        count = fetch_table_count(conn, table_name) if table_exists(conn, table_name) else 0
        lines.append(f"| `{table_name}` | {count} |")

    lines.extend(
        [
            "",
            "## Exclusions",
            "",
            "- Silver/Gold/dashboard work not started in this step.",
            "- Streetcar ingestion excluded from core MVP scope.",
            "- GTFS-RT polling DAG execution deferred.",
            "",
            "## Output Files",
            "",
            "- `raw/` registries (CSV + Parquet)",
            "- `bronze/` table exports (Parquet)",
            "- `configs/schema_bus.yml`",
            "- `configs/schema_subway.yml`",
            "- `docs/source_inventory.md`",
            "- `logs/ingestion_log.csv`",
            "- `docs/step1_summary.md`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_project_structure()
    ensure_duckdb_database()
    append_ingestion_log(
        step="project_setup",
        status="SUCCESS",
        row_count=0,
        output_path=to_rel_posix(DB_PATH),
        details="Project structure and DuckDB file ensured.",
    )
    print(f"Project setup complete. Database: {DB_PATH}")


if __name__ == "__main__":
    main()


