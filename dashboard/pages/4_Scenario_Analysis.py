"""Scenario analysis page with an explicit Phase 5B availability state."""

from pathlib import Path

import streamlit as st

from src.utils.config import RESULTS_DIR, REPORTS_DIR


st.title("Scenario Analysis")
scenario_files = list(RESULTS_DIR.glob("scenario*")) + list(REPORTS_DIR.glob("scenario*"))
if not scenario_files:
    st.info("Scenario analysis has not been generated yet. Complete Phase 5B to enable this page.")
    st.write(
        "No scenario CSV, JSON, or verification report was found. This dashboard does not "
        "generate scenario results implicitly."
    )
    st.stop()

st.warning("Scenario outputs were found, but a dedicated Phase 5B scenario schema is required before display.")
