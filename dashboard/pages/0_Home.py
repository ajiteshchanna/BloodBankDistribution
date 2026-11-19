"""Home dashboard page."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.common import load_data
from dashboard.components.tables import show_kpis


st.title("Blood Bank Distribution & Emergency Allocation")
st.markdown(
    "An Operations Research system for optimizing simulated blood distribution while "
    "prioritizing emergency demand."
)
st.caption("Academic simulation using synthetic data; not intended for clinical decision support.")

data = load_data()
requests = data["requests"]
inventory = data["inventory"]
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
steps = st.columns(6)
for step, label in zip(steps, ["Dataset", "Validation", "Optimization", "Verification", "Results", "Analysis"]):
    step.markdown(f"**{label}**")

left, right = st.columns(2)
with left:
    st.subheader("Formulations")
    st.markdown(
        "- **Transportation LP:** continuous aggregate shipments.\n"
        "- **Assignment MILP:** integer request shipments with one assigned bank at most.\n"
        "- **Integrated MILP:** request-level transportation and assignment. The current "
        "Assignment and Integrated implementations are mathematically equivalent."
    )
with right:
    st.subheader("Assumptions")
    st.markdown(
        "- Synthetic academic dataset.\n"
        "- Exact ABO/Rh matching only.\n"
        "- Emergency-first lexicographic optimization.\n"
        "- Explicit shortage variables.\n"
        "- Not a clinical decision-support system."
    )
