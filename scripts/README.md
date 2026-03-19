# Scripts

## DuckDB analytical layer

- `setup_duckdb.sh` initializes `data/ttc.duckdb`, builds partitioned Parquet delays data, and creates analytical views.
- `verify_duckdb.sh` runs connection, aggregation, partition-pruning, and basic runtime checks.

Usage:

```bash
scripts/setup_duckdb.sh
scripts/verify_duckdb.sh
```
