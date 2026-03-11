"""Utilities for loading TTC bus delay data for 2023 and 2024."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


COLUMN_ALIASES: Dict[str, str] = {
    "date": "date",
    "report_date": "date",
    "incident_date": "date",
    "time": "time",
    "report_time": "time",
    "incident_time": "time",
    "route": "route",
    "route_number": "route",
    "line": "route",
    "day": "day",
    "location": "location",
    "intersection": "location",
    "incident": "incident",
    "incident_type": "incident",
    "delay_reason": "incident",
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


def _best_effort_standardize(df: pd.DataFrame) -> pd.DataFrame:
    """Build a standardized dataframe even when column headers vary by source."""
    standardized = pd.DataFrame(index=df.index)

    if "date" in df.columns:
        standardized["date"] = df["date"]

    # Some TTC exports provide full timestamp instead of separate date/time columns.
    timestamp_col = next((c for c in ("datetime", "timestamp") if c in df.columns), None)
    if "time" not in df.columns and timestamp_col is not None:
        parsed = pd.to_datetime(df[timestamp_col], errors="coerce")
        standardized["time"] = parsed.dt.strftime("%H:%M")
        if "date" not in standardized:
            standardized["date"] = parsed.dt.date

    if "time" in df.columns:
        standardized["time"] = df["time"]

    for col in ("route", "location", "incident", "min_delay", "min_gap"):
        if col in df.columns:
            standardized[col] = df[col]

    if "min_gap" not in standardized.columns and "min_delay" in standardized.columns:
        standardized["min_gap"] = standardized["min_delay"]

    for col in OPTIONAL_COLUMNS:
        if col in df.columns:
            standardized[col] = df[col]

    return standardized


def load_year_data(file_path: str | Path, year: int) -> pd.DataFrame:
    """Load a single year's file and return a standardized dataframe."""
    df = _read_csv_with_fallback(file_path)
    df.columns = [_normalize_column_name(c) for c in df.columns]

    df = _best_effort_standardize(df)
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


def load_multiple_files(file_paths: list[str | Path]) -> pd.DataFrame:
    """Load one or more TTC delay CSV files and infer year from file content/name."""
    merged: list[pd.DataFrame] = []

    for file_path in file_paths:
        path = Path(file_path)
        raw = _read_csv_with_fallback(path)
        raw.columns = [_normalize_column_name(c) for c in raw.columns]
        standardized = _best_effort_standardize(raw)

        missing = [c for c in REQUIRED_COLUMNS if c not in standardized.columns]
        if missing:
            raise ValueError(f"Missing required columns in {path}: {missing}")

        year = _infer_year(standardized, path)
        output_columns = REQUIRED_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in standardized.columns]
        standardized = standardized[output_columns].copy()
        standardized["year"] = year
        merged.append(standardized)

    if not merged:
        return pd.DataFrame(columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS + ["year"])

    return pd.concat(merged, ignore_index=True)


def _infer_year(df: pd.DataFrame, file_path: Path) -> int:
    """Infer year using date column first, then filename fallback."""
    parsed_dates = pd.to_datetime(df.get("date"), errors="coerce")
    if not parsed_dates.isna().all():
        mode_year = parsed_dates.dt.year.dropna()
        if not mode_year.empty:
            return int(mode_year.mode().iloc[0])

    match = next((token for token in file_path.stem.split("_") if token.isdigit() and len(token) == 4), None)
    if match is not None:
        return int(match)

    return 0
