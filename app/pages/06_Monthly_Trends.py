from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import line_chart
from ttc_pulse.dashboard.loaders import load_monthly_trends

st.title("6. Monthly Trends")

df = load_monthly_trends()
if df.empty:
    st.warning("Monthly trends are unavailable.")
else:
    metric = st.selectbox("Metric", ["event_count", "avg_delay", "p90_delay"], index=0)
    chart = line_chart(
        df,
        x="month:T",
        y=f"{metric}:Q",
        color="mode:N",
        title=f"Monthly {metric}",
    )
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, use_container_width=True)
