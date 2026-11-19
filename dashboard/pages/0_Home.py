"""Home dashboard page."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.common import load_data
from dashboard.components.charts import demand_distribution_chart
from dashboard.components.tables import show_kpis, show_workflow


st.markdown('<div class="eyebrow">OPERATIONS RESEARCH DASHBOARD</div>', unsafe_allow_html=True)
st.title("Blood Bank Distribution & Emergency Allocation")
st.markdown(
    "An Operations Research system for optimizing simulated blood distribution while "
    "prioritizing emergency demand."
)
st.caption("Academic simulation using synthetic data. Not intended for clinical decision support.")

data = load_data()
requests = data["requests"]
inventory = data["inventory"]
emergency_demand = int(requests.loc[requests["priority"] == "Emergency", "required_units"].sum())
normal_demand = int(requests.loc[requests["priority"] == "Normal", "required_units"].sum())
total_demand = emergency_demand + normal_demand

show_kpis(
    {
        "Blood banks": len(data["blood_banks"]),
        "Hospitals": len(data["hospitals"]),
        "Blood groups": inventory["blood_group"].nunique(),
        "Available units": int(inventory["available_units"].sum()),
        "Requested units": int(requests["required_units"].sum()),
        "Emergency demand": emergency_demand,
        "Normal demand": normal_demand,
    },
    columns=5,
    highlighted={"Emergency demand"},
)

st.header("Project overview")
st.write(
    "Blood banks have limited quantities of different blood groups, while hospitals submit "
    "emergency and normal requests. The models determine feasible allocations and prioritize "
    "emergency shortages before normal shortages and transportation cost."
)

left, right = st.columns([1, 1.4])
with left:
    st.subheader("Emergency demand")
    share = emergency_demand / total_demand if total_demand else 0
    st.metric("Units", emergency_demand)
    st.caption(f"{share:.1%} of total requested demand")
with right:
    demand_distribution_chart(
        pd.DataFrame(
            [
                {"category": "Emergency", "units": emergency_demand, "share": share},
                {
                    "category": "Normal",
                    "units": normal_demand,
                    "share": normal_demand / total_demand if total_demand else 0,
                },
            ]
        )
    )

st.header("Optimization workflow")
show_workflow(["Dataset", "Validation", "Optimization", "Verification", "Results", "Analysis"])

left, right = st.columns(2)
with left:
    st.subheader("Optimization formulations")
    st.markdown(
        "- **Transportation LP:** continuous aggregate shipments.\n"
        "- **Assignment MILP:** integer request shipments with one assigned bank at most.\n"
        "- **Integrated MILP:** request-level transportation and assignment. The current "
        "Assignment and Integrated implementations are mathematically equivalent."
    )
with right:
    st.subheader("Important assumptions")
    st.markdown(
        "- Synthetic academic dataset.\n"
        "- Exact ABO/Rh matching only.\n"
        "- Emergency-first lexicographic optimization.\n"
        "- Explicit shortage variables.\n"
        "- Not a clinical decision-support system."
    )
