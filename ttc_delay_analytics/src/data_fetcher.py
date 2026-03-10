"""Download TTC bus delay CSV resources from Toronto Open Data CKAN."""

from __future__ import annotations

from pathlib import Path

import requests

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_URL = f"{BASE_URL}/api/3/action/package_show"


def fetch_ttc_delay_csvs(output_dir: str | Path) -> None:
    """Download 2023 and 2024 TTC bus delay CSV files into output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    package = requests.get(PACKAGE_URL, params={"id": "ttc-bus-delay-data"}, timeout=30).json()
    resources = package["result"]["resources"]

    for resource in resources:
        name = (resource.get("name") or "").lower()
        url = resource.get("url")
        if not url or "csv" not in url.lower():
            continue

        if "2023" in name:
            target = output_dir / "ttc_bus_delay_2023.csv"
        elif "2024" in name:
            target = output_dir / "ttc_bus_delay_2024.csv"
        else:
            continue

        response = requests.get(url, timeout=60)
        response.raise_for_status()
        target.write_bytes(response.content)
        print(f"Downloaded: {target}")


if __name__ == "__main__":
    fetch_ttc_delay_csvs(Path(__file__).resolve().parents[1] / "data")
