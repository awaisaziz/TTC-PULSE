from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from ttc_pulse.utils.project_setup import ROOT_DIR, append_ingestion_log, ensure_project_structure, to_rel_posix, utc_now_iso

RAW_SNAPSHOTS_DIR = ROOT_DIR / "alerts" / "raw_snapshots"


def poll_once(url: str | None, timeout_seconds: int = 30) -> Path:
    ensure_project_structure()
    RAW_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp_token = utc_now_iso().replace(":", "").replace("-", "")

    if not url:
        snapshot_path = RAW_SNAPSHOTS_DIR / f"gtfsrt_alert_snapshot_stub_{timestamp_token}.json"
        payload = {
            "snapshot_generated_utc": utc_now_iso(),
            "source": "stub",
            "alerts": [],
            "note": "No GTFSRT_ALERTS_URL configured. Stub snapshot generated for pipeline continuity.",
        }
        snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        append_ingestion_log(
            step="poll_service_alerts",
            status="SUCCESS",
            row_count=1,
            output_path=to_rel_posix(snapshot_path),
            details="Generated stub snapshot because URL was not configured.",
        )
        return snapshot_path

    request = Request(url, headers={"User-Agent": "ttc-pulse-step3/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        content_type = (response.headers.get("Content-Type") or "").lower()
        payload = response.read()

    extension = "json" if "json" in content_type else "pb"
    snapshot_path = RAW_SNAPSHOTS_DIR / f"gtfsrt_alert_snapshot_{timestamp_token}.{extension}"
    if extension == "pb":
        with snapshot_path.open("wb") as output_file:
            output_file.write(payload)
    else:
        with snapshot_path.open("w", encoding="utf-8") as output_file:
            output_file.write(payload.decode("utf-8", errors="replace"))

    append_ingestion_log(
        step="poll_service_alerts",
        status="SUCCESS",
        row_count=1,
        output_path=to_rel_posix(snapshot_path),
        details=f"Fetched GTFS-RT snapshot from {url}.",
    )
    return snapshot_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll GTFS-RT service alerts and persist a raw snapshot.")
    parser.add_argument("--url", default=os.getenv("GTFSRT_ALERTS_URL"), help="GTFS-RT service alerts URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    args = parser.parse_args()

    snapshot_path = poll_once(url=args.url, timeout_seconds=args.timeout)
    print(f"raw_snapshot={snapshot_path}")


if __name__ == "__main__":
    main()
