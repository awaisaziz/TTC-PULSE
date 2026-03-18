from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.loaders import load_kpi_snapshot
from ttc_pulse.dashboard.formatting import as_int

st.set_page_config(page_title="TTC Pulse - Reliability Observatory", layout="wide")

st.title("TTC Pulse - Reliability Observatory")
st.caption("Step 4 MVP Dashboard | DuckDB + Parquet backend | Spark excluded")

kpi_df = load_kpi_snapshot()
if not kpi_df.empty:
    row = kpi_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Delay Events", as_int(row.get("delay_events")))
    c2.metric("Ranked Entities", as_int(row.get("ranked_entities")))
    c3.metric("Route Review Queue", as_int(row.get("route_review_rows")))
    c4.metric("Station Review Queue", as_int(row.get("station_review_rows")))

st.markdown("""
Use the pages in the left sidebar in the locked panel order:
1. Linkage QA panel
2. Reliability overview
3. Bus route ranking
4. Subway station ranking
5. Weekday x hour heatmap
6. Monthly trends
7. Cause/category mix
8. Live alert validation panel
9. Spatial hotspot map (placeholder)
""")
