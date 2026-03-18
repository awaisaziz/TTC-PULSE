from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import bar_chart
from ttc_pulse.dashboard.loaders import load_top_offender_ranking

st.title("4. Subway Station Ranking")

limit = st.slider("Top N", min_value=10, max_value=200, value=50, step=10)
df = load_top_offender_ranking(entity_type="station", mode="subway", limit=limit)

if df.empty:
    st.warning("No subway station ranking data available.")
else:
    chart = bar_chart(
        df.sort_values("offender_rank").head(limit),
        x="entity_key:N",
        y="reliability_composite_score:Q",
        title="Top Subway Station Offenders by Composite Score",
    )
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, use_container_width=True)
