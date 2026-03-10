"""Exploratory data analysis helpers for TTC bus delay project."""

from __future__ import annotations

import pandas as pd


def temporal_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return delays grouped by hour, day of week, and month."""
    return {
        "by_hour": df.groupby("hour").size().reset_index(name="delay_count"),
        "by_day_of_week": df.groupby("day_of_week").size().reset_index(name="delay_count"),
        "by_month": df.groupby("month", observed=True).size().reset_index(name="delay_count"),
    }


def route_analysis(df: pd.DataFrame, top_n: int = 15) -> dict[str, pd.DataFrame]:
    """Return route frequency and average delay summaries."""
    return {
        "highest_frequency": df.groupby("route").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(top_n),
        "highest_avg_delay": df.groupby("route", as_index=False)["min_delay"].mean().rename(columns={"min_delay": "avg_delay"}).sort_values("avg_delay", ascending=False).head(top_n),
    }


def incident_analysis(df: pd.DataFrame, top_n: int = 15) -> dict[str, pd.DataFrame]:
    """Return incident frequency and average delay by incident type."""
    return {
        "common_reasons": df.groupby("incident").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(top_n),
        "avg_delay_by_incident": df.groupby("incident", as_index=False)["min_delay"].mean().rename(columns={"min_delay": "avg_delay"}).sort_values("avg_delay", ascending=False).head(top_n),
    }


def spatial_analysis(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Return top delay locations by frequency."""
    return df.groupby("location").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(top_n)


def comparison_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame | pd.Series]:
    """Compare 2023 vs 2024 totals, averages, and grouped metrics."""
    year_summary = df.groupby("year").agg(
        total_delays=("min_delay", "size"),
        avg_delay=("min_delay", "mean"),
    ).reset_index()

    delays_by_route = df.groupby(["year", "route"]).size().reset_index(name="delay_count")
    delays_by_incident = df.groupby(["year", "incident"]).size().reset_index(name="delay_count")

    return {
        "year_summary": year_summary,
        "delays_by_route": delays_by_route,
        "delays_by_incident": delays_by_incident,
    }
