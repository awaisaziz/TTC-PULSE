from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.charts import bar_chart
from ttc_pulse.dashboard.loaders import load_alert_pipeline_status, load_alert_validation

st.title("8. Live Alert Validation Panel")

status_df = load_alert_pipeline_status()
if not status_df.empty:
    row = status_df.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Raw Snapshots", int(row.get("raw_snapshot_rows", 0)))
    c2.metric("Bronze Entities", int(row.get("bronze_alert_entities", 0)))
    c3.metric("Silver Entities", int(row.get("silver_alert_entities", 0)))
    c4.metric("Fact Alerts", int(row.get("fact_alert_rows", 0)))
    c5.metric("Gold Validation Rows", int(row.get("gold_validation_rows", 0)))

validation_df = load_alert_validation()
if validation_df.empty:
    st.warning(
        "No validation rows found. Run the side-car chain: poll -> register -> parse -> normalize -> fact -> gold validation."
    )
else:
    summary = (
        validation_df.groupby("validation_status", as_index=False)
        .size()
        .rename(columns={"size": "rows"})
        .sort_values("rows", ascending=False)
    )
    chart = bar_chart(summary, x="validation_status:N", y="rows:Q", title="Alert Validation Status")
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)

    only_health = st.toggle("Show snapshot-health rows only", value=False)
    if only_health:
        filtered = validation_df[validation_df["match_method"] == "snapshot_health"].copy()
    else:
        filtered = validation_df

    st.dataframe(filtered, use_container_width=True)
