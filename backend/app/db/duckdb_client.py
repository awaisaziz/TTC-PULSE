from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class TTLCache:
    """Small in-memory TTL cache for query responses."""

    def __init__(self, ttl_seconds: int = 30, max_items: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self.max_items:
                oldest_key = next(iter(self._store))
                self._store.pop(oldest_key, None)
            self._store[key] = (time.time() + self.ttl_seconds, value)


class DuckDBClient:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.getenv("DUCKDB_PATH", "data/ttc.duckdb")
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.Lock()
        self.cache = TTLCache(ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "30")))

    def _resolve_db_path(self) -> Path:
        configured = Path(self.db_path).expanduser()
        if configured.is_absolute():
            return configured

        cwd_candidate = Path.cwd() / configured
        if cwd_candidate.exists():
            return cwd_candidate

        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / configured

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self._conn is not None:
            return self._conn

        path = self._resolve_db_path()
        if not path.exists():
            raise FileNotFoundError(
                f"DuckDB file not found at '{path}'. Run scripts/run_pipeline.py first."
            )

        self._conn = duckdb.connect(str(path), read_only=True)
        self._conn.execute("PRAGMA threads=4;")
        self._conn.execute("PRAGMA enable_progress_bar=false;")
        logger.info("Connected to DuckDB at %s", path)
        return self._conn

    def query(self, sql: str, params: Sequence[Any] | None = None, cache_key: str | None = None) -> list[dict[str, Any]]:
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for key=%s", cache_key)
                return cached

        start = time.perf_counter()
        with self._lock:
            conn = self.connect()
            result = conn.execute(sql, params or []).fetchdf()

        duration = time.perf_counter() - start
        logger.info("DuckDB query completed in %.3fs", duration)

        payload = result.to_dict(orient="records")
        if cache_key:
            self.cache.set(cache_key, payload)
        return payload


_db_client: DuckDBClient | None = None


def get_db_client() -> DuckDBClient:
    global _db_client
    if _db_client is None:
        _db_client = DuckDBClient()
    return _db_client
