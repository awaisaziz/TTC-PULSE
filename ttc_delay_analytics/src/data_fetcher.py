"""Download TTC bus delay CSV resources from Toronto Open Data CKAN."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_URL = f"{BASE_URL}/api/3/action/package_show"
RESOURCE_SHOW_URL = f"{BASE_URL}/api/3/action/resource_show"
DATASTORE_SEARCH_URL = f"{BASE_URL}/api/3/action/datastore_search"


def _get_json(url: str, *, params: dict[str, Any], timeout: int) -> dict[str, Any]:
    """Perform an HTTP GET request and return JSON payload."""
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


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
    """Download full resource data, preferring datastore pagination when available."""
    if resource.get("datastore_active"):
        _download_datastore_resource_csv(resource["id"], target)
        return

    # Some resources expose metadata where the direct downloadable URL is more reliable.
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
    target.write_bytes(response.content)


def fetch_ttc_delay_csvs(output_dir: str | Path) -> None:
    """Download 2023 and 2024 TTC bus delay CSV files into output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    package = _get_json(PACKAGE_URL, params={"id": "ttc-bus-delay-data"}, timeout=30)
    resources = package["result"]["resources"]

    for resource in resources:
        name = (resource.get("name") or "").lower()

        if "2023" in name:
            target = output_dir / "ttc_bus_delay_2023.csv"
        elif "2024" in name:
            target = output_dir / "ttc_bus_delay_2024.csv"
        else:
            continue

        _download_resource_csv(resource, target)
        print(f"Downloaded full dataset: {target}")


if __name__ == "__main__":
    fetch_ttc_delay_csvs(Path(__file__).resolve().parents[1] / "data")
