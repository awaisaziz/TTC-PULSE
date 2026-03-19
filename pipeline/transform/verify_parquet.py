from __future__ import annotations

from pathlib import Path

import duckdb


def run_verification(parquet_root: Path = Path("data/parquet")) -> None:
    con = duckdb.connect()
    query = f"""
    SELECT
      COUNT(*) AS total_rows,
      COUNT_IF(vehicle_type = 'subway' AND incident_code IS NOT NULL AND incident_desc IS NOT NULL) AS mapped_subway_codes,
      COUNT(DISTINCT source_file) AS source_files
    FROM read_parquet('{parquet_root.as_posix()}/**/*.parquet', hive_partitioning=1)
    """
    result = con.execute(query).fetchdf()
    print(result.to_string(index=False))


if __name__ == "__main__":
    run_verification()
