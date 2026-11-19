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
    .block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 2rem; }
    [data-testid="stMetric"] {
        background: #202024;
        border: 1px solid #303036;
        border-radius: 10px;
        padding: 12px;
    }
    [data-testid="stButton"] button {
        border-radius: 8px;
        border: 1px solid #E63946;
    }
    [data-testid="stDownloadButton"] button {
        border-radius: 8px;
        border: 1px solid #303036;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #E63946;
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
        "Project": [
            st.Page(str(pages_dir / "6_About.py"), title="About"),
        ],
    },
    position="top",
)
navigation.run()
