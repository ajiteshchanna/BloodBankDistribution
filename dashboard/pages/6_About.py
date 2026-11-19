"""About page describing the academic model and limitations."""

import streamlit as st

st.title("About the Project")
st.caption("Academic Operations Research simulation")
st.header("Problem statement and objectives")
st.write(
    "The project allocates limited packed RBC inventory from blood banks to hospital requests. "
    "Emergency requests receive lexicographic priority, while transport eligibility, deadlines, "
    "inventory, and cost are respected."
)
st.write(
    "The objective is to maximize useful fulfillment through a lexicographic hierarchy: minimize "
    "emergency unmet units, then normal unmet units, then transportation cost."
)
st.header("Dataset")
st.write(
    "The project uses five synthetic blood banks, eight hospitals, eight exact ABO/Rh groups, "
    "inventory records, hospital requests, and a simplified transportation network."
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
st.latex(r"\sum_i q_{ir} + u_r = d_r")
st.latex(r"\sum_{r:g(r)=g} q_{ir} \leq S_{ig}")
st.header("Technology and limitations")
st.markdown(
    "Python, Pandas, Gurobi, Streamlit, and Plotly are used. The dataset is synthetic academic data. "
    "The model is not a clinical tool, has no real-time connectivity, and does not implement full "
    "medical compatibility, expiry, or patient-level decision logic."
)
