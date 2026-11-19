"""About page describing the academic model and limitations."""

import streamlit as st

st.title("About the Project")
st.header("Problem statement")
st.write(
    "The project allocates limited packed RBC inventory from blood banks to hospital requests. "
    "Emergency requests receive lexicographic priority, while transport eligibility, deadlines, "
    "inventory, and cost are respected."
)
st.header("Operations Research techniques")
st.markdown(
    "- Linear programming and the classical transportation problem.\n"
    "- Integer programming and assignment optimization.\n"
    "- Mixed-integer linear programming.\n"
    "- Lexicographic multi-objective optimization."
)
st.header("Model concepts")
st.markdown(
    "Shipment variables represent units sent from banks to requests. Binary assignment variables "
    "select at most one bank per request in the MILP models. Inventory and request-balance constraints "
    "conserve units, while eligibility enforces exact blood-group matching and delivery deadlines."
)
st.header("Technology and limitations")
st.markdown(
    "Python, Pandas, Gurobi, Streamlit, and Plotly are used. The dataset is synthetic academic data. "
    "The model is not a clinical tool, has no real-time connectivity, and does not implement full "
    "medical compatibility, expiry, or patient-level decision logic."
)
