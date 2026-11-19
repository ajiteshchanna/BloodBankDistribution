"""Project overview entry point for the Streamlit dashboard."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.loader import load_all_datasets
from dashboard.components.tables import show_kpis


@st.cache_data
def load_data():
    return load_all_datasets()


st.set_page_config(
    page_title="Blood Bank Distribution Optimization",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    "<style>.block-container{padding-top:2rem;padding-bottom:2rem}"
    "h1,h2,h3{color:#16324f}.stMetric{border:1px solid #d9e2ec;padding:12px;border-radius:6px}</style>",
    unsafe_allow_html=True,
)

data = load_data()
requests = data["requests"]
inventory = data["inventory"]
st.title("Blood Bank Distribution and Emergency Hospital Allocation")
st.markdown(
    "An academic Operations Research dashboard for allocating simulated packed red blood cell "
    "units while respecting inventory, delivery eligibility, emergency priority, and transport cost."
)
show_kpis({
    "Blood banks": len(data["blood_banks"]),
    "Hospitals": len(data["hospitals"]),
    "Blood groups": inventory["blood_group"].nunique(),
    "Available units": int(inventory["available_units"].sum()),
    "Requested units": int(requests["required_units"].sum()),
    "Emergency demand": int(requests.loc[requests["priority"] == "Emergency", "required_units"].sum()),
    "Normal demand": int(requests.loc[requests["priority"] == "Normal", "required_units"].sum()),
})

st.header("Project overview")
st.write(
    "Blood banks have limited quantities of different blood groups, while hospitals submit "
    "emergency and normal requests. The models determine feasible allocations and prioritize "
    "emergency shortages before normal shortages and transportation cost."
)

st.header("Optimization workflow")
st.markdown("**Dataset → Validation → Optimization → Verification → Results → Comparison**")

left, right = st.columns(2)
with left:
    st.subheader("Formulations")
    st.markdown(
        "- **Transportation LP:** continuous aggregate shipments.\n"
        "- **Assignment MILP:** integer request shipments with one assigned bank at most.\n"
        "- **Integrated MILP:** request-level transportation and assignment formulation."
    )
with right:
    st.subheader("Important assumptions")
    st.markdown(
        "- Synthetic teaching data, not operational hospital data.\n"
        "- Exact ABO/Rh matching only.\n"
        "- No clinical decision support or patient-level compatibility logic.\n"
        "- Shortages are explicitly modeled rather than hidden."
    )
