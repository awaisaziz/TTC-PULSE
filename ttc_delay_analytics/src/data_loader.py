"""Utilities for loading TTC bus delay data for 2023 and 2024."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


COLUMN_ALIASES: Dict[str, str] = {
    "date": "date",
    "report_date": "date",
    "time": "time",
    "report_time": "time",
    "route": "route",
    "route_number": "route",
    "day": "day",
    "location": "location",
    "incident": "incident",
    "min delay": "min_delay",
    "min_delay": "min_delay",
    "delay": "min_delay",
    "min gap": "min_gap",
    "min_gap": "min_gap",
    "gap": "min_gap",
    "vehicle": "vehicle",
}


REQUIRED_COLUMNS = ["date", "time", "route", "location", "incident", "min_delay", "min_gap"]


def _normalize_column_name(col: str) -> str:
    """Normalize column names into snake_case and map aliases."""
    normalized = col.strip().lower().replace(" ", "_")
    return COLUMN_ALIASES.get(normalized, normalized)


def load_year_data(file_path: str | Path, year: int) -> pd.DataFrame:
    """Load a single year's file and return a standardized dataframe."""
    df = pd.read_csv(file_path)
    df.columns = [_normalize_column_name(c) for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")

    standardized = df[REQUIRED_COLUMNS].copy()
    standardized["year"] = year
    return standardized


def load_and_merge_data(data_dir: str | Path) -> pd.DataFrame:
    """Load TTC bus delay CSV files for 2023 and 2024 and combine them."""
    data_dir = Path(data_dir)
    file_2023 = data_dir / "ttc_bus_delay_2023.csv"
    file_2024 = data_dir / "ttc_bus_delay_2024.csv"

    df_2023 = load_year_data(file_2023, 2023)
    df_2024 = load_year_data(file_2024, 2024)

    return pd.concat([df_2023, df_2024], ignore_index=True)
