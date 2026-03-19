#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.ingest.ingest_pipeline import MasterIngestionAgent

if TYPE_CHECKING:
    import duckdb


def run_sql_file(conn, sql_path: Path) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    conn.execute(sql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TTC ingestion pipeline and initialize DuckDB analytics layer.")
    parser.add_argument("--raw-root", default="data/raw", help="Input raw data folder")
    parser.add_argument("--processed-root", default="data/processed", help="Output cleaned CSV folder")
    parser.add_argument("--parquet-root", default="data/parquet", help="Output parquet folder")
    parser.add_argument("--db-path", default="data/ttc.duckdb", help="DuckDB database path")
    args = parser.parse_args()

    raw_root = ROOT_DIR / args.raw_root
    processed_root = ROOT_DIR / args.processed_root
    parquet_root = ROOT_DIR / args.parquet_root
    db_path = ROOT_DIR / args.db_path

    agent = MasterIngestionAgent(
        raw_root=raw_root,
        processed_root=processed_root,
        parquet_root=parquet_root,
        log_path=ROOT_DIR / "pipeline/ingest/ingestion.log",
    )

    unified, results, checks, quality = agent.run()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    import duckdb

    conn = duckdb.connect(str(db_path))
    try:
        run_sql_file(conn, ROOT_DIR / "sql/duckdb/01_initialize.sql")
        run_sql_file(conn, ROOT_DIR / "sql/duckdb/02_optimized_views.sql")
    finally:
        conn.close()

    summary = {
        "rows_written": int(len(unified)),
        "files_total": len(results),
        "files_processed": sum(1 for r in results if r.status == "processed"),
        "files_failed": sum(1 for r in results if r.status == "failed"),
        "verification": checks,
        "quality": quality,
        "duckdb_path": str(db_path),
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
