from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "ttc_pulse.duckdb"


def _connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


def table_exists(table_name: str) -> bool:
    try:
        with _connect() as conn:
            result = conn.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'main' AND table_name = ?;
                """,
                [table_name],
            ).fetchone()[0]
        return bool(result)
    except Exception:
        return False


def query_df(sql: str, params: list[Any] | None = None) -> pd.DataFrame:
    try:
        with _connect() as conn:
            return conn.execute(sql, params or []).df()
    except Exception:
        return pd.DataFrame()


def load_gold_linkage_quality() -> pd.DataFrame:
    return query_df("SELECT * FROM gold_linkage_quality ORDER BY dataset, mode;")


def load_gold_time_reliability() -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_time_reliability
        ORDER BY mode, weekday_name, hour_of_day;
        """
    )


def load_gold_route_time_metrics(mode: str = "bus") -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_route_time_metrics
        WHERE mode = ?
        ORDER BY reliability_composite_score DESC;
        """,
        [mode],
    )


def load_gold_station_time_metrics(mode: str = "subway") -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_station_time_metrics
        WHERE mode = ?
        ORDER BY reliability_composite_score DESC;
        """,
        [mode],
    )


def load_top_offender_ranking(entity_type: str, mode: str, limit: int = 50) -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_top_offender_ranking
        WHERE entity_type = ? AND mode = ?
        ORDER BY offender_rank
        LIMIT ?;
        """,
        [entity_type, mode, limit],
    )


def load_monthly_trends() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            mode,
            date_trunc('month', event_date)::DATE AS month,
            COUNT(*) AS event_count,
            AVG(delay_minutes) AS avg_delay,
            quantile_cont(delay_minutes, 0.9) AS p90_delay
        FROM gold_delay_events_core
        GROUP BY 1, 2
        ORDER BY 2, 1;
        """
    )


def load_cause_mix(limit_per_mode: int = 20) -> pd.DataFrame:
    return query_df(
        """
        WITH base AS (
            SELECT
                mode,
                coalesce(nullif(trim(incident_code_raw), ''), 'UNKNOWN') AS incident_code,
                COUNT(*) AS event_count,
                AVG(delay_minutes) AS avg_delay
            FROM gold_delay_events_core
            GROUP BY 1, 2
        ),
        ranked AS (
            SELECT
                *,
                row_number() OVER (PARTITION BY mode ORDER BY event_count DESC, incident_code) AS rn
            FROM base
        )
        SELECT mode, incident_code, event_count, avg_delay
        FROM ranked
        WHERE rn <= ?
        ORDER BY mode, event_count DESC;
        """,
        [limit_per_mode],
    )


def load_alert_validation() -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_alert_validation
        ORDER BY coalesce(snapshot_timestamp_ts, generated_at_utc) DESC NULLS LAST;
        """
    )


def load_alert_pipeline_status() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            (SELECT COUNT(*) FROM raw_gtfsrt_alert_snapshots_registry) AS raw_snapshot_rows,
            (SELECT COUNT(*) FROM bronze_gtfsrt_alert_entities) AS bronze_alert_entities,
            (SELECT COUNT(*) FROM silver_gtfsrt_alert_entities) AS silver_alert_entities,
            (SELECT COUNT(*) FROM fact_gtfsrt_alerts_norm) AS fact_alert_rows,
            (SELECT COUNT(*) FROM gold_alert_validation) AS gold_validation_rows;
        """
    )


def load_gold_delay_core_sample(limit: int = 50000) -> pd.DataFrame:
    return query_df(
        """
        SELECT *
        FROM gold_delay_events_core
        ORDER BY event_ts DESC NULLS LAST
        LIMIT ?;
        """,
        [limit],
    )


def load_spatial_hotspot(mode: str | None = None, only_passed: bool = False, limit: int = 5000) -> pd.DataFrame:
    filters = []
    params: list[Any] = []

    if mode:
        filters.append("mode = ?")
        params.append(mode)
    if only_passed:
        filters.append("confidence_gate_passed = TRUE")

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    params.append(limit)

    return query_df(
        f"""
        SELECT *
        FROM gold_spatial_hotspot
        {where_clause}
        ORDER BY hotspot_score DESC NULLS LAST
        LIMIT ?;
        """,
        params,
    )


def load_kpi_snapshot() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            (SELECT COUNT(*) FROM gold_delay_events_core) AS delay_events,
            (SELECT COUNT(*) FROM gold_top_offender_ranking) AS ranked_entities,
            (SELECT COUNT(*) FROM route_alias_review) AS route_review_rows,
            (SELECT COUNT(*) FROM station_alias_review) AS station_review_rows,
            (SELECT COUNT(*) FROM incident_code_review) AS incident_code_review_rows,
            (SELECT COUNT(*) FROM gold_alert_validation) AS alert_validation_rows;
        """
    )
