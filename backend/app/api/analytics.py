from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.duckdb_client import DuckDBClient, get_db_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analytics"])


def _timed_response(endpoint: str, started_at: float) -> None:
    elapsed = time.perf_counter() - started_at
    logger.info("Endpoint %s served in %.3fs", endpoint, elapsed)


@router.get("/routes")
def get_routes(db: Annotated[DuckDBClient, Depends(get_db_client)]) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            d.route_id,
            d.vehicle_type,
            COUNT(*)::BIGINT AS event_count,
            ROUND(AVG(d.min_delay), 2) AS avg_delay
        FROM delays d
        GROUP BY d.route_id, d.vehicle_type
        ORDER BY event_count DESC
        LIMIT 200
        """
        data = db.query(sql, cache_key="routes:v1")
        _timed_response("/routes", started)
        return {"count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch routes")
        raise HTTPException(status_code=500, detail="Failed to fetch routes") from exc


@router.get("/delay")
def get_delay(
    route_id: Annotated[str, Query(min_length=1, max_length=64)],
    vehicle_type: Annotated[str | None, Query(pattern="^(bus|subway)$")] = None,
    db: DuckDBClient = Depends(get_db_client),
) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            route_id,
            vehicle_type,
            COUNT(*)::BIGINT AS event_count,
            ROUND(AVG(min_delay), 2) AS avg_delay,
            ROUND(quantile_cont(min_delay, 0.50), 2) AS p50_delay,
            ROUND(quantile_cont(min_delay, 0.90), 2) AS p90_delay,
            MAX(min_delay) AS max_delay
        FROM delays
        WHERE route_id = ?
          AND (? IS NULL OR vehicle_type = ?)
        GROUP BY route_id, vehicle_type
        """
        params = [route_id, vehicle_type, vehicle_type]
        cache_key = f"delay:{route_id}:{vehicle_type or 'all'}"
        data = db.query(sql, params=params, cache_key=cache_key)
        _timed_response("/delay", started)
        return {"route_id": route_id, "count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch delay stats for route_id=%s", route_id)
        raise HTTPException(status_code=500, detail="Failed to fetch delay data") from exc


@router.get("/stats")
def get_stats(db: Annotated[DuckDBClient, Depends(get_db_client)]) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            vehicle_type,
            COUNT(*)::BIGINT AS total_events,
            COUNT(DISTINCT route_id)::BIGINT AS total_routes,
            ROUND(AVG(min_delay), 2) AS avg_delay,
            ROUND(quantile_cont(min_delay, 0.90), 2) AS p90_delay
        FROM delays
        GROUP BY vehicle_type
        ORDER BY total_events DESC
        """
        data = db.query(sql, cache_key="stats:v1")
        _timed_response("/stats", started)
        return {"count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch stats")
        raise HTTPException(status_code=500, detail="Failed to fetch stats") from exc


@router.get("/heatmap")
def get_heatmap(
    vehicle_type: Annotated[str | None, Query(pattern="^(bus|subway)$")] = None,
    days: Annotated[int | None, Query(ge=1, le=365)] = None,
    db: DuckDBClient = Depends(get_db_client),
) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            EXTRACT('dow' FROM service_date)::INTEGER AS day_of_week,
            EXTRACT('hour' FROM service_time)::INTEGER AS hour_of_day,
            vehicle_type,
            COUNT(*)::BIGINT AS event_count,
            ROUND(AVG(min_delay), 2) AS avg_delay
        FROM delays
        WHERE (? IS NULL OR vehicle_type = ?)
          AND (? IS NULL OR service_date >= CURRENT_DATE - (? * INTERVAL '1 day'))
        GROUP BY day_of_week, hour_of_day, vehicle_type
        ORDER BY day_of_week, hour_of_day, vehicle_type
        """
        params = [vehicle_type, vehicle_type, days, days]
        cache_key = f"heatmap:v2:{vehicle_type or 'all'}:{days or 'all'}"
        data = db.query(sql, params=params, cache_key=cache_key)
        _timed_response("/heatmap", started)
        return {"count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch heatmap")
        raise HTTPException(status_code=500, detail="Failed to fetch heatmap") from exc


@router.get("/top-routes")
def get_top_routes(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    min_events: Annotated[int, Query(ge=10, le=10000)] = 100,
    vehicle_type: Annotated[str | None, Query(pattern="^(bus|subway)$")] = None,
    days: Annotated[int | None, Query(ge=1, le=365)] = None,
    db: DuckDBClient = Depends(get_db_client),
) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            route_id,
            vehicle_type,
            COUNT(*)::BIGINT AS event_count,
            ROUND(AVG(min_delay), 2) AS avg_delay,
            ROUND(quantile_cont(min_delay, 0.90), 2) AS p90_delay
        FROM delays
        WHERE (? IS NULL OR vehicle_type = ?)
          AND (? IS NULL OR service_date >= CURRENT_DATE - (? * INTERVAL '1 day'))
        GROUP BY route_id, vehicle_type
        HAVING COUNT(*) >= ?
        ORDER BY avg_delay DESC, p90_delay DESC
        LIMIT ?
        """
        params = [vehicle_type, vehicle_type, days, days, min_events, limit]
        cache_key = f"top:v2:{limit}:{min_events}:{vehicle_type or 'all'}:{days or 'all'}"
        data = db.query(sql, params=params, cache_key=cache_key)
        _timed_response("/top-routes", started)
        return {"count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch top routes")
        raise HTTPException(status_code=500, detail="Failed to fetch top routes") from exc


@router.get("/delay-trend")
def get_delay_trend(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    route_id: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    vehicle_type: Annotated[str | None, Query(pattern="^(bus|subway)$")] = None,
    db: DuckDBClient = Depends(get_db_client),
) -> dict:
    started = time.perf_counter()
    try:
        sql = """
        SELECT
            service_date,
            route_id,
            vehicle_type,
            COUNT(*)::BIGINT AS event_count,
            ROUND(AVG(min_delay), 2) AS avg_delay,
            ROUND(quantile_cont(min_delay, 0.90), 2) AS p90_delay
        FROM delays
        WHERE service_date >= CURRENT_DATE - (? * INTERVAL '1 day')
          AND (? IS NULL OR route_id = ?)
          AND (? IS NULL OR vehicle_type = ?)
        GROUP BY service_date, route_id, vehicle_type
        ORDER BY service_date
        """
        params = [days, route_id, route_id, vehicle_type, vehicle_type]
        cache_key = f"trend:v1:{days}:{route_id or 'all'}:{vehicle_type or 'all'}"
        data = db.query(sql, params=params, cache_key=cache_key)
        _timed_response("/delay-trend", started)
        return {"count": len(data), "data": data}
    except Exception as exc:
        logger.exception("Failed to fetch delay trend")
        raise HTTPException(status_code=500, detail="Failed to fetch delay trend") from exc
