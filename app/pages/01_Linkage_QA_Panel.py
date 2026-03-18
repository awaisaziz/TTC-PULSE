from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import bar_chart
from ttc_pulse.dashboard.formatting import as_float, as_int, as_pct
from ttc_pulse.dashboard.loaders import load_gold_linkage_quality, query_df

st.title("1. Linkage QA Panel")

df = load_gold_linkage_quality()
if df.empty:
    st.warning("gold_linkage_quality is empty or unavailable.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Datasets", as_int(df["dataset"].nunique()))
    c2.metric("Modes", as_int(df["mode"].nunique()))
    c3.metric("Avg Linked Rate", as_pct(df["linked_rate"].mean()))

    chart = bar_chart(df, x="mode:N", y="linked_rate:Q", color="dataset:N", title="Linked Rate by Dataset/Mode")
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)

    st.dataframe(df, use_container_width=True)

review_df = query_df(
    """
    SELECT 'route_alias_review' AS review_table, COUNT(*) AS review_rows FROM route_alias_review
    UNION ALL
    SELECT 'station_alias_review', COUNT(*) FROM station_alias_review
    UNION ALL
    SELECT 'incident_code_review', COUNT(*) FROM incident_code_review
    ORDER BY review_rows DESC;
    """
)
st.subheader("Review Queue")
if not review_df.empty:
    chart = bar_chart(review_df, x="review_table:N", y="review_rows:Q", title="Rows Pending Review")
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(review_df, use_container_width=True)
else:
    st.info("Review tables not available.")
