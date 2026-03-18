from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ttc_pulse.dashboard.loaders import load_spatial_hotspot

st.title("9. Spatial Hotspot Map")

mode = st.selectbox("Mode", ["all", "bus", "subway"], index=0)
only_passed = st.toggle("Only confidence-gate passed hotspots", value=True)
limit = st.slider("Max hotspots", min_value=100, max_value=5000, value=1000, step=100)

selected_mode = None if mode == "all" else mode
hotspot_df = load_spatial_hotspot(mode=selected_mode, only_passed=only_passed, limit=limit)

if hotspot_df.empty:
    st.warning(
        "No spatial hotspot rows available for the current filter. "
        "Try disabling the confidence gate filter or rebuilding gold_delay_events_core."
    )
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(hotspot_df))
    c2.metric("Gate Passed", int(hotspot_df["confidence_gate_passed"].sum()))
    c3.metric("Max Score", f"{hotspot_df['hotspot_score'].max():.3f}")

    map_df = hotspot_df[["stop_lat", "stop_lon"]].rename(columns={"stop_lat": "lat", "stop_lon": "lon"})
    st.map(map_df, use_container_width=True)

    st.dataframe(
        hotspot_df[
            [
                "mode",
                "station_key",
                "stop_name",
                "freq_events",
                "hotspot_score",
                "avg_match_confidence",
                "confidence_gate_passed",
                "confidence_gate_reason",
            ]
        ],
        use_container_width=True,
    )
