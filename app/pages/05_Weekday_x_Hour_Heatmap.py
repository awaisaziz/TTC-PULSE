from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import heatmap
from ttc_pulse.dashboard.loaders import load_gold_time_reliability

st.title("5. Weekday x Hour Heatmap")

df = load_gold_time_reliability()
if df.empty:
    st.warning("gold_time_reliability is empty or unavailable.")
else:
    mode = st.selectbox("Mode", sorted(df["mode"].dropna().unique().tolist()))
    metric = st.selectbox(
        "Metric",
        ["reliability_composite_score", "freq_events", "sev90_delay", "reg90_gap", "cause_mix"],
        index=0,
    )
    filtered = df[df["mode"] == mode].copy()

    chart = heatmap(
        filtered,
        x="hour_of_day:O",
        y="weekday_name:N",
        color=f"{metric}:Q",
        title=f"{mode.title()} {metric} Heatmap",
    )
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(filtered.sort_values(["weekday_name", "hour_of_day"]), use_container_width=True)
