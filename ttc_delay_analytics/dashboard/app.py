"""Streamlit app for TTC bus delay analytics."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data_loader import TARGET_YEAR, load_and_merge_data, load_multiple_uploads
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
def load_default_data():
    raw = load_and_merge_data(ROOT / "data")
    return clean_and_transform(raw)


@st.cache_data
def load_uploaded_data(file_names: tuple[str, ...], file_bytes: tuple[bytes, ...]):
    uploads = list(zip(file_names, file_bytes))
    raw = load_multiple_uploads(uploads)
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


def render_overview(df):
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

    st.plotly_chart(delay_distribution_histogram(df), use_container_width=True)
    st.plotly_chart(delay_vs_gap_scatter_plot(df), use_container_width=True)


def render_temporal(df):
    st.subheader("Temporal Analysis")
    st.plotly_chart(delays_by_hour_heatmap(df), use_container_width=True)
    st.plotly_chart(delay_trends_by_month(df), use_container_width=True)


def render_route(df):
    st.subheader("Route Reliability")
    st.plotly_chart(top_routes_bar_chart(df), use_container_width=True)


def render_incident(df):
    st.subheader("Incident Causes")
    st.plotly_chart(incident_type_bar_chart(df), use_container_width=True)


def render_location(df):
    st.subheader("Location Hotspots")
    hotspots = spatial_analysis(df)
    st.dataframe(hotspots, use_container_width=True)


def render_combined_dashboard(df):
    st.subheader("Combined Live Dashboard")
    options = {
        "Overview": render_overview,
        "Temporal analysis": render_temporal,
        "Route reliability": render_route,
        "Incident causes": render_incident,
        "Location hotspots": render_location,
    }
    selected_sections = st.multiselect(
        "Select analyses to display",
        list(options.keys()),
        default=["Overview", "Temporal analysis"],
    )

    for section in selected_sections:
        st.markdown("---")
        options[section](df)


def load_data_from_ui():
    st.sidebar.header("Dataset Source")
    source = st.sidebar.radio("Choose dataset", [f"Default {TARGET_YEAR} file", f"Upload CSV file(s) ({TARGET_YEAR} only)"])

    if source == f"Default {TARGET_YEAR} file":
        return load_default_data()

    uploaded_files = st.sidebar.file_uploader(
        f"Upload one or more TTC delay CSV files ({TARGET_YEAR} only)",
        type=["csv"],
        accept_multiple_files=True,
    )
    if not uploaded_files:
        st.info("Upload at least one CSV file to continue.")
        st.stop()

    names = tuple(uploaded_file.name for uploaded_file in uploaded_files)
    payloads = tuple(uploaded_file.getvalue() for uploaded_file in uploaded_files)
    return load_uploaded_data(names, payloads)


def main():
    st.set_page_config(page_title="TTC Delay Analytics", layout="wide")
    st.title("TTC Bus Delay Analytics Dashboard")

    try:
        df = load_data_from_ui()
    except FileNotFoundError:
        st.error(f"Default CSV file not found. Place ttc_bus_delay_{TARGET_YEAR}.csv in ttc_delay_analytics/data/ or upload CSVs from the sidebar.")
        st.stop()
    except ValueError as exc:
        st.error(f"Unable to load selected dataset: {exc}")
        st.stop()

    filtered_df = apply_filters(df)
    if filtered_df.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    page = st.sidebar.radio(
        "Page",
        [
            "Overview",
            "Temporal analysis",
            "Route reliability",
            "Incident causes",
            "Location hotspots",
            "Combined dashboard",
        ],
    )

    if page == "Overview":
        render_overview(filtered_df)
    elif page == "Temporal analysis":
        render_temporal(filtered_df)
    elif page == "Route reliability":
        render_route(filtered_df)
    elif page == "Incident causes":
        render_incident(filtered_df)
    elif page == "Location hotspots":
        render_location(filtered_df)
    else:
        render_combined_dashboard(filtered_df)


if __name__ == "__main__":
    main()
