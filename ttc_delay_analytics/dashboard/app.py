"""Streamlit app for TTC bus delay analytics."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data_loader import load_and_merge_data
from src.eda_analysis import comparison_analysis, spatial_analysis
from src.preprocessing import clean_and_transform
from src.visualization import (
    delay_distribution_histogram,
    delay_trends_by_month,
    delay_vs_gap_scatter_plot,
    delays_by_hour_heatmap,
    incident_type_bar_chart,
    top_routes_bar_chart,
)


@st.cache_data
def load_data():
    raw = load_and_merge_data(ROOT / "data")
    return clean_and_transform(raw)


def apply_filters(df):
    st.sidebar.header("Filters")

    years = st.sidebar.multiselect("Year", sorted(df["year"].unique()), default=sorted(df["year"].unique()))
    routes = st.sidebar.multiselect("Route", sorted(df["route"].astype(str).unique()))
    incidents = st.sidebar.multiselect("Incident Type", sorted(df["incident"].astype(str).unique()))
    severities = st.sidebar.multiselect(
        "Delay Severity",
        ["minor", "moderate", "major", "critical", "unknown"],
        default=["minor", "moderate", "major", "critical", "unknown"],
    )

    filtered = df[df["year"].isin(years)]
    if routes:
        filtered = filtered[filtered["route"].astype(str).isin(routes)]
    if incidents:
        filtered = filtered[filtered["incident"].astype(str).isin(incidents)]
    if severities:
        filtered = filtered[filtered["delay_severity"].isin(severities)]

    return filtered


def overview_page(df):
    st.subheader("Overview")
    c1, c2 = st.columns(2)
    c1.metric("Total Delays", f"{len(df):,}")
    c2.metric("Average Delay (minutes)", f"{df['min_delay'].mean():.2f}")

    summary = comparison_analysis(df)["year_summary"]
    st.dataframe(summary, use_container_width=True)

    top_route = df.groupby("route").size().sort_values(ascending=False).head(1)
    top_incident = df.groupby("incident").size().sort_values(ascending=False).head(1)
    top_location = df.groupby("location").size().sort_values(ascending=False).head(1)

    i1, i2, i3 = st.columns(3)
    i1.metric("Most impacted route", str(top_route.index[0]) if len(top_route) else "N/A")
    i2.metric("Most common incident", str(top_incident.index[0]) if len(top_incident) else "N/A")
    i3.metric("Top hotspot", str(top_location.index[0]) if len(top_location) else "N/A")

    if "direction" in df.columns:
        st.caption("Direction breakdown")
        st.dataframe(df.groupby("direction").size().reset_index(name="delay_count").sort_values("delay_count", ascending=False).head(10), use_container_width=True)

    st.plotly_chart(delay_distribution_histogram(df), use_container_width=True)
    st.plotly_chart(delay_vs_gap_scatter_plot(df), use_container_width=True)


def temporal_page(df):
    st.subheader("Temporal Analysis")
    st.plotly_chart(delays_by_hour_heatmap(df), use_container_width=True)
    st.plotly_chart(delay_trends_by_month(df), use_container_width=True)


def route_page(df):
    st.subheader("Route Reliability")
    st.plotly_chart(top_routes_bar_chart(df), use_container_width=True)


def incident_page(df):
    st.subheader("Incident Causes")
    st.plotly_chart(incident_type_bar_chart(df), use_container_width=True)


def location_page(df):
    st.subheader("Location Hotspots")
    hotspots = spatial_analysis(df)
    st.dataframe(hotspots, use_container_width=True)


def main():
    st.set_page_config(page_title="TTC Delay Analytics", layout="wide")
    st.title("TTC Bus Delay Analytics Dashboard (2023 vs 2024)")

    try:
        df = load_data()
    except FileNotFoundError:
        st.error(
            "CSV files not found. Place ttc_bus_delay_2023.csv and ttc_bus_delay_2024.csv in ttc_delay_analytics/data/."
        )
        st.stop()

    filtered_df = apply_filters(df)
    if filtered_df.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    page = st.sidebar.radio(
        "Page",
        ["Overview", "Temporal analysis", "Route reliability", "Incident causes", "Location hotspots"],
    )

    if page == "Overview":
        overview_page(filtered_df)
    elif page == "Temporal analysis":
        temporal_page(filtered_df)
    elif page == "Route reliability":
        route_page(filtered_df)
    elif page == "Incident causes":
        incident_page(filtered_df)
    else:
        location_page(filtered_df)


if __name__ == "__main__":
    main()
