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
    "direction": "direction",
    "vehicle": "vehicle",
}


REQUIRED_COLUMNS = ["date", "time", "route", "location", "incident", "min_delay", "min_gap"]
OPTIONAL_COLUMNS = ["day", "direction", "vehicle"]


def _normalize_column_name(col: str) -> str:
    """Normalize column names into snake_case and map aliases."""
    normalized = col.strip().lower().replace(" ", "_")
    return COLUMN_ALIASES.get(normalized, normalized)


def load_year_data(file_path: str | Path, year: int) -> pd.DataFrame:
    """Load a single year's file and return a standardized dataframe."""
    df = _read_csv_with_fallback(file_path)
    df.columns = [_normalize_column_name(c) for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")

    output_columns = REQUIRED_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in df.columns]
    standardized = df[output_columns].copy()
    standardized["year"] = year
    return standardized


def _read_csv_with_fallback(file_path: str | Path) -> pd.DataFrame:
    """Read a delimited file while handling common encoding/parser issues.

    Strategy:
    1) Try strict parsing first (no row skipping) across common encodings and
       delimiters (auto-detect/comma/tab/semicolon).
    2) If strict parsing fails due malformed rows, retry with bad-line skipping
       so dashboard loading can still proceed with clean rows.
    """
    file_path = Path(file_path)

    encodings = ("utf-8", "utf-8-sig", "cp1252", "latin1")
    separators: tuple[str | None, ...] = (None, ",", "\t", ";")
    attempted_errors: list[str] = []

    for encoding in encodings:
        for separator in separators:
            sep_label = "auto" if separator is None else repr(separator)
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=separator,
                    engine="python",
                    on_bad_lines="error",
                )
            except (UnicodeDecodeError, pd.errors.ParserError) as exc:
                attempted_errors.append(f"strict encoding={encoding}, sep={sep_label}: {exc}")

    for encoding in encodings:
        for separator in separators:
            sep_label = "auto" if separator is None else repr(separator)
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=separator,
                    engine="python",
                    on_bad_lines="skip",
                )
            except (UnicodeDecodeError, pd.errors.ParserError) as exc:
                attempted_errors.append(f"skip-bad-lines encoding={encoding}, sep={sep_label}: {exc}")

    raise ValueError(
        "Unable to parse data file "
        f"{file_path}. Tried encodings={encodings} and delimiters=('auto', ',', '\t', ';'). "
        f"Last parser/decoder errors: {attempted_errors[-4:]}"
    )


def load_and_merge_data(data_dir: str | Path) -> pd.DataFrame:
    """Load TTC bus delay CSV files for 2023 and 2024 and combine them."""
    data_dir = Path(data_dir)
    file_2023 = data_dir / "ttc_bus_delay_2023.csv"
    file_2024 = data_dir / "ttc_bus_delay_2024.csv"

    df_2023 = load_year_data(file_2023, 2023)
    df_2024 = load_year_data(file_2024, 2024)

    return pd.concat([df_2023, df_2024], ignore_index=True)
