from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import line_chart
from ttc_pulse.dashboard.formatting import as_float, as_int
from ttc_pulse.dashboard.loaders import load_gold_time_reliability

st.title("2. Reliability Overview")

df = load_gold_time_reliability()
if df.empty:
    st.warning("gold_time_reliability is empty or unavailable.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", as_int(len(df)))
    c2.metric("Mean Composite", as_float(df["reliability_composite_score"].mean(), 3))
    c3.metric("p90 Composite", as_float(df["reliability_composite_score"].quantile(0.9), 3))

    mode = st.selectbox("Mode", sorted(df["mode"].dropna().unique().tolist()))
    filtered = df[df["mode"] == mode].copy()
    filtered["time_key"] = filtered["weekday_name"].astype(str) + " " + filtered["hour_of_day"].astype(str)

    chart = line_chart(
        filtered,
        x="hour_of_day:Q",
        y="reliability_composite_score:Q",
        color="weekday_name:N",
        title=f"Reliability Composite by Hour ({mode})",
    )
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)

    st.dataframe(
        filtered.sort_values(["weekday_name", "hour_of_day"]),
        use_container_width=True,
    )
