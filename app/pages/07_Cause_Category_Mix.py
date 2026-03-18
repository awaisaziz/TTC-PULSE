from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import stacked_bar
from ttc_pulse.dashboard.loaders import load_cause_mix

st.title("7. Cause/Category Mix")

limit = st.slider("Top causes per mode", min_value=5, max_value=30, value=15, step=5)
df = load_cause_mix(limit_per_mode=limit)

if df.empty:
    st.warning("Cause/category mix data is unavailable.")
else:
    chart = stacked_bar(
        df,
        x="mode:N",
        y="event_count:Q",
        stack_color="incident_code:N",
        title="Incident Code Mix by Mode",
    )
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, use_container_width=True)
