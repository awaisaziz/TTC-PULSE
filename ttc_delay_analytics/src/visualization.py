"""Plotly visualization utilities for TTC delay analytics dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def delay_distribution_histogram(df: pd.DataFrame):
    return px.histogram(df, x="min_delay", nbins=40, title="Delay Distribution (minutes)")


def delays_by_hour_heatmap(df: pd.DataFrame):
    pivot = (
        df.groupby(["day_of_week", "hour"]).size().reset_index(name="delay_count")
        .pivot(index="day_of_week", columns="hour", values="delay_count")
        .fillna(0)
    )
    return px.imshow(
        pivot,
        labels={"x": "Hour", "y": "Day of Week", "color": "Delay Count"},
        title="Delays by Hour Heatmap",
        aspect="auto",
    )


def delay_trends_by_month(df: pd.DataFrame):
    monthly = df.groupby(["year", "month"], observed=True).size().reset_index(name="delay_count")
    return px.line(monthly, x="month", y="delay_count", color="year", markers=True, title="Delay Trends by Month")


def top_routes_bar_chart(df: pd.DataFrame, top_n: int = 15):
    top_routes = df.groupby("route").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(top_n)
    return px.bar(top_routes, x="route", y="delay_count", title=f"Top {top_n} Routes by Delay Frequency")


def incident_type_bar_chart(df: pd.DataFrame, top_n: int = 15):
    incidents = df.groupby("incident").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(top_n)
    return px.bar(incidents, x="incident", y="delay_count", title=f"Top {top_n} Incident Types")


def delay_vs_gap_scatter_plot(df: pd.DataFrame):
    sampled = df.sample(min(len(df), 3000), random_state=42) if len(df) else df
    return px.scatter(
        sampled,
        x="min_gap",
        y="min_delay",
        color="year",
        hover_data=["route", "incident", "location"],
        title="Delay vs Gap",
        opacity=0.7,
    )
