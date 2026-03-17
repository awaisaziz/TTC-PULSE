"""Download TTC bus delay datasets and store them as CSV files."""

from __future__ import annotations

import csv
from io import BytesIO
from pathlib import Path
import re
from typing import Any

import pandas as pd
import requests

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_URL = f"{BASE_URL}/api/3/action/package_show"
RESOURCE_SHOW_URL = f"{BASE_URL}/api/3/action/resource_show"
DATASTORE_SEARCH_URL = f"{BASE_URL}/api/3/action/datastore_search"
BUS_PACKAGE_ID = "ttc-bus-delay-data"
SKIP_TOKENS = ("readme", "code description")


def _get_json(url: str, *, params: dict[str, Any], timeout: int) -> dict[str, Any]:
    """Perform an HTTP GET request and return JSON payload."""
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _slugify(name: str) -> str:
    """Create a stable filesystem-safe file stem from a CKAN resource name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "resource"


def _download_datastore_resource_csv(resource_id: str, target: Path, page_size: int = 50_000) -> None:
    """Write all datastore records to CSV via paginated CKAN API calls."""
    offset = 0
    writer: csv.DictWriter[str] | None = None

    with target.open("w", newline="", encoding="utf-8") as output_file:
        while True:
            payload = _get_json(
                DATASTORE_SEARCH_URL,
                params={"resource_id": resource_id, "limit": page_size, "offset": offset},
                timeout=60,
            )

            if not payload.get("success"):
                raise RuntimeError(f"Failed to fetch datastore records for resource {resource_id}")

            result = payload["result"]
            if writer is None:
                field_names = [field["id"] for field in result.get("fields", []) if field["id"] != "_id"]
                writer = csv.DictWriter(output_file, fieldnames=field_names, extrasaction="ignore")
                writer.writeheader()

            page_records = result.get("records", [])
            if not page_records:
                break

            writer.writerows(page_records)
            offset += len(page_records)


def _download_resource_csv(resource: dict[str, Any], target: Path) -> None:
    """Download resource data and ensure the output is CSV."""
    if resource.get("datastore_active"):
        _download_datastore_resource_csv(resource["id"], target)
        return

    resource_id = resource.get("id")
    resource_url = resource.get("url")
    if resource_id:
        metadata = _get_json(RESOURCE_SHOW_URL, params={"id": resource_id}, timeout=30)
        if metadata.get("success"):
            resource_url = metadata["result"].get("url") or resource_url

    if not resource_url:
        raise RuntimeError(f"No URL found for resource {resource_id}")

    response = requests.get(resource_url, timeout=120)
    response.raise_for_status()

    content = response.content
    is_excel_payload = content[:2] == b"PK"
    if is_excel_payload:
        excel_df = pd.read_excel(BytesIO(content))
        excel_df.to_csv(target, index=False)
        return

    target.write_bytes(content)


def fetch_ttc_bus_delay_csvs(output_dir: str | Path) -> None:
    """Download all TTC bus delay resources into output_dir/bus as CSV files."""
    output_dir = Path(output_dir) / "bus"
    output_dir.mkdir(parents=True, exist_ok=True)

    package = _get_json(PACKAGE_URL, params={"id": BUS_PACKAGE_ID}, timeout=30)
    resources = package["result"]["resources"]

    downloaded = 0
    for resource in resources:
        name = (resource.get("name") or resource.get("id") or "resource").strip()
        normalized_name = name.lower()
        if any(token in normalized_name for token in SKIP_TOKENS):
            continue

        target = output_dir / f"{_slugify(name)}.csv"
        _download_resource_csv(resource, target)
        downloaded += 1
        print(f"Downloaded bus dataset: {target}")

    print(f"Completed. Downloaded {downloaded} bus resource file(s) into {output_dir}.")


def fetch_ttc_delay_csvs(output_dir: str | Path) -> None:
    """Backward-compatible alias for bus delay fetch workflow."""
    fetch_ttc_bus_delay_csvs(output_dir)


if __name__ == "__main__":
    fetch_ttc_bus_delay_csvs(Path(__file__).resolve().parents[1] / "data")
