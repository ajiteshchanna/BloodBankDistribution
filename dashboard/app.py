"""Streamlit entry point with native top navigation."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Blood Bank Optimization",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    .block-container { max-width: 1440px; padding-top: 1.25rem; padding-bottom: 2rem; }
    .eyebrow {
        color: #E63946;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        margin-bottom: 0.5rem;
    }
    .kpi-highlight-label {
        color: #E63946;
        font-size: 0.8rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.35rem;
    }
    [data-testid="stMetric"] {
        background: #202024;
        border: 1px solid #303036;
        border-radius: 10px;
        padding: 0.75rem;
    }
    .workflow-arrow {
        color: #E63946;
        font-size: 1.4rem;
        text-align: center;
        padding-top: 1.1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages_dir = Path(__file__).parent / "pages"
navigation = st.navigation(
    {
        "Overview": [
            st.Page(str(pages_dir / "0_Home.py"), title="Home"),
            st.Page(str(pages_dir / "1_Dataset_Overview.py"), title="Dataset Overview"),
        ],
        "Optimization": [
            st.Page(str(pages_dir / "2_Run_Optimization.py"), title="Run Optimization"),
            st.Page(str(pages_dir / "3_Results.py"), title="Results"),
        ],
        "Analysis": [
            st.Page(str(pages_dir / "4_Scenario_Analysis.py"), title="Scenario Analysis"),
            st.Page(str(pages_dir / "5_Model_Comparison.py"), title="Model Comparison"),
        ],
        "Project": [st.Page(str(pages_dir / "6_About.py"), title="About")],
    },
    position="top",
)
navigation.run()
