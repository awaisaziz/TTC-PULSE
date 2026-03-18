from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    from google.transit import gtfs_realtime_pb2  # type: ignore
except Exception:  # pragma: no cover
    gtfs_realtime_pb2 = None

from ttc_pulse.utils.project_setup import (
    ROOT_DIR,
    append_ingestion_log,
    connect_duckdb,
    copy_table_to_parquet,
    ensure_duckdb_database,
    ensure_project_structure,
    fetch_table_count,
    sql_quote,
    to_rel_posix,
    utc_now_iso,
)

RAW_SNAPSHOTS_DIR = ROOT_DIR / "alerts" / "raw_snapshots"
PARSED_DIR = ROOT_DIR / "alerts" / "parsed"
PARSED_JSONL = PARSED_DIR / "gtfsrt_alert_entities_latest.jsonl"
TABLE_NAME = "bronze_gtfsrt_alert_entities"
BRONZE_PARQUET = ROOT_DIR / "bronze" / "bronze_gtfsrt_alert_entities.parquet"


def _to_utc_iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except Exception:
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            try:
                return datetime.fromtimestamp(float(stripped), tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            except Exception:
                return stripped
        return stripped
    return None


def _extract_nested_text(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("translation", "text"):
            if key in value:
                nested = value[key]
                if isinstance(nested, list) and nested:
                    candidate = nested[0]
                    if isinstance(candidate, dict):
                        text = candidate.get("text")
                        if isinstance(text, str) and text.strip():
                            return text.strip()
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return None


def _base_row(snapshot_path: Path, index: int) -> dict[str, object]:
    return {
        "snapshot_id": snapshot_path.stem,
        "snapshot_timestamp_utc": utc_now_iso(),
        "entity_index": index,
        "lineage_source_file": to_rel_posix(snapshot_path),
        "lineage_source_row_number": index + 1,
        "lineage_bronze_loaded_at_utc": utc_now_iso(),
        "lineage_source_registry": "raw_gtfsrt_alert_snapshots_registry",
    }


def _parse_json_snapshot(snapshot_path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    entities = []
    if isinstance(payload, dict):
        if isinstance(payload.get("entity"), list):
            entities = payload["entity"]
        elif isinstance(payload.get("alerts"), list):
            entities = payload["alerts"]

    rows: list[dict[str, object]] = []
    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        alert = entity.get("alert") if isinstance(entity.get("alert"), dict) else entity
        informed = alert.get("informed_entity") if isinstance(alert.get("informed_entity"), list) and alert.get("informed_entity") else []
        informed_first = informed[0] if informed and isinstance(informed[0], dict) else {}
        active_period = alert.get("active_period") if isinstance(alert.get("active_period"), list) and alert.get("active_period") else []
        active_first = active_period[0] if active_period and isinstance(active_period[0], dict) else {}

        row = {
            "alert_id": str(entity.get("id") or alert.get("id") or "").strip() or None,
            "active_period_start_utc": _to_utc_iso(active_first.get("start")),
            "active_period_end_utc": _to_utc_iso(active_first.get("end")),
            "cause": str(alert.get("cause") or "").strip() or None,
            "effect": str(alert.get("effect") or "").strip() or None,
            "severity_level": str(alert.get("severity_level") or "").strip() or None,
            "header_text": _extract_nested_text(alert.get("header_text")),
            "description_text": _extract_nested_text(alert.get("description_text")),
            "url": _extract_nested_text(alert.get("url")),
            "informed_entity_route_id": str(informed_first.get("route_id") or "").strip() or None,
            "informed_entity_stop_id": str(informed_first.get("stop_id") or "").strip() or None,
            "informed_entity_trip_id": str((informed_first.get("trip") or {}).get("trip_id") if isinstance(informed_first.get("trip"), dict) else "") or None,
        }
        row.update(_base_row(snapshot_path, index))
        rows.append(row)
    return rows


def _parse_pb_snapshot(snapshot_path: Path) -> list[dict[str, object]]:
    if gtfs_realtime_pb2 is None:
        return []

    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(snapshot_path.read_bytes())
    except Exception:
        return []

    rows: list[dict[str, object]] = []
    for index, entity in enumerate(feed.entity):
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        informed_first = alert.informed_entity[0] if len(alert.informed_entity) > 0 else None
        active_first = alert.active_period[0] if len(alert.active_period) > 0 else None

        header_text = None
        if alert.header_text and len(alert.header_text.translation) > 0:
            header_text = alert.header_text.translation[0].text.strip() if alert.header_text.translation[0].text else None

        description_text = None
        if alert.description_text and len(alert.description_text.translation) > 0:
            description_text = alert.description_text.translation[0].text.strip() if alert.description_text.translation[0].text else None

        url = None
        if alert.url and len(alert.url.translation) > 0:
            url = alert.url.translation[0].text.strip() if alert.url.translation[0].text else None

        cause = gtfs_realtime_pb2.Alert.Cause.Name(alert.cause) if alert.HasField("cause") else None
        effect = gtfs_realtime_pb2.Alert.Effect.Name(alert.effect) if alert.HasField("effect") else None

        severity = None
        if hasattr(alert, "severity_level") and alert.HasField("severity_level"):
            try:
                severity = gtfs_realtime_pb2.Alert.SeverityLevel.Name(alert.severity_level)
            except Exception:
                severity = str(alert.severity_level)

        row = {
            "alert_id": entity.id.strip() if entity.id else None,
            "active_period_start_utc": _to_utc_iso(active_first.start) if active_first and active_first.HasField("start") else None,
            "active_period_end_utc": _to_utc_iso(active_first.end) if active_first and active_first.HasField("end") else None,
            "cause": cause,
            "effect": effect,
            "severity_level": severity,
            "header_text": header_text,
            "description_text": description_text,
            "url": url,
            "informed_entity_route_id": informed_first.route_id.strip() if informed_first and informed_first.HasField("route_id") else None,
            "informed_entity_stop_id": informed_first.stop_id.strip() if informed_first and informed_first.HasField("stop_id") else None,
            "informed_entity_trip_id": informed_first.trip.trip_id.strip() if informed_first and informed_first.HasField("trip") and informed_first.trip.HasField("trip_id") else None,
        }
        row.update(_base_row(snapshot_path, index))
        rows.append(row)
    return rows


def parse_snapshots() -> int:
    ensure_project_structure()
    ensure_duckdb_database()
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_files = [f for f in sorted(RAW_SNAPSHOTS_DIR.glob("*")) if f.is_file() and not f.name.startswith(".")]
    parsed_rows: list[dict[str, object]] = []
    parsed_sources = 0

    for snapshot_path in snapshot_files:
        rows: list[dict[str, object]] = []
        suffix = snapshot_path.suffix.lower()
        if suffix == ".json":
            rows = _parse_json_snapshot(snapshot_path)
        elif suffix == ".pb":
            rows = _parse_pb_snapshot(snapshot_path)
        parsed_rows.extend(rows)
        if rows:
            parsed_sources += 1

    with PARSED_JSONL.open("w", encoding="utf-8") as output_file:
        for row in parsed_rows:
            output_file.write(json.dumps(row, ensure_ascii=True) + "\n")

    with connect_duckdb() as conn:
        if parsed_rows:
            conn.execute(
                f"""
                CREATE OR REPLACE TABLE {TABLE_NAME} AS
                SELECT
                    cast(alert_id as varchar) AS alert_id,
                    cast(active_period_start_utc as varchar) AS active_period_start_utc,
                    cast(active_period_end_utc as varchar) AS active_period_end_utc,
                    cast(cause as varchar) AS cause,
                    cast(effect as varchar) AS effect,
                    cast(severity_level as varchar) AS severity_level,
                    cast(header_text as varchar) AS header_text,
                    cast(description_text as varchar) AS description_text,
                    cast(url as varchar) AS url,
                    cast(informed_entity_route_id as varchar) AS informed_entity_route_id,
                    cast(informed_entity_stop_id as varchar) AS informed_entity_stop_id,
                    cast(informed_entity_trip_id as varchar) AS informed_entity_trip_id,
                    cast(snapshot_id as varchar) AS snapshot_id,
                    cast(snapshot_timestamp_utc as varchar) AS snapshot_timestamp_utc,
                    cast(entity_index as bigint) AS entity_index,
                    cast(lineage_source_file as varchar) AS lineage_source_file,
                    cast(lineage_source_row_number as bigint) AS lineage_source_row_number,
                    cast(lineage_bronze_loaded_at_utc as varchar) AS lineage_bronze_loaded_at_utc,
                    cast(lineage_source_registry as varchar) AS lineage_source_registry
                FROM read_json_auto({sql_quote(PARSED_JSONL.resolve().as_posix())});
                """
            )
        else:
            conn.execute(
                f"""
                CREATE OR REPLACE TABLE {TABLE_NAME} (
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

        copy_table_to_parquet(conn, TABLE_NAME, BRONZE_PARQUET)
        row_count = fetch_table_count(conn, TABLE_NAME)

    append_ingestion_log(
        step="parse_service_alerts",
        status="SUCCESS",
        row_count=row_count,
        output_path=to_rel_posix(BRONZE_PARQUET),
        details=(
            f"snapshots_scanned={len(snapshot_files)};"
            f"sources_with_entities={parsed_sources};"
            f"parsed_entities={row_count};"
            f"protobuf_parser={'enabled' if gtfs_realtime_pb2 is not None else 'disabled'}"
        ),
    )
    return row_count


def main() -> None:
    row_count = parse_snapshots()
    print(f"{TABLE_NAME}: {row_count}")


if __name__ == "__main__":
    main()
