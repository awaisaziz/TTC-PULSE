"""Data cleaning and feature engineering for TTC delay data."""

from __future__ import annotations

import pandas as pd


def classify_delay_severity(minutes: float) -> str:
    """Assign severity bucket from delay minutes."""
    if pd.isna(minutes):
        return "unknown"
    if minutes <= 5:
        return "minor"
    if minutes <= 15:
        return "moderate"
    if minutes <= 30:
        return "major"
    return "critical"


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw dataframe and create derived fields for analysis."""
    cleaned = df.copy()

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["time"] = pd.to_datetime(cleaned["time"], format="%H:%M", errors="coerce")

    cleaned["min_delay"] = pd.to_numeric(cleaned["min_delay"], errors="coerce")
    cleaned["min_gap"] = pd.to_numeric(cleaned["min_gap"], errors="coerce")

    # Handle missing values for key categorical fields.
    for col in ["route", "location", "incident"]:
        cleaned[col] = cleaned[col].fillna("Unknown")

    cleaned = cleaned.dropna(subset=["date", "min_delay"])

    cleaned["hour"] = cleaned["time"].dt.hour.fillna(0).astype(int)
    cleaned["day_of_week"] = cleaned["date"].dt.day_name()
    cleaned["month"] = cleaned["date"].dt.month_name()
    cleaned["delay_severity"] = cleaned["min_delay"].apply(classify_delay_severity)

    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    cleaned["month"] = pd.Categorical(cleaned["month"], categories=month_order, ordered=True)

    return cleaned
