"""Run a selected verified Gurobi model on demand."""

import streamlit as st

from dashboard.common import load_data, run_selected_model, validation_summary
from dashboard.components.tables import show_kpis, show_status


st.title("Run Optimization")
model_name = st.selectbox("Optimization model", [
    "Transportation LP", "Assignment MILP", "Integrated MILP",
])
descriptions = {
    "Transportation LP": "Continuous aggregate shipments by hospital and blood group.",
    "Assignment MILP": "Integer request shipments with at most one supplying bank.",
    "Integrated MILP": "Request-level transportation and assignment; currently equivalent to Assignment MILP.",
}
st.caption(descriptions[model_name])

with st.expander("Dataset validation", expanded=False):
    validation_data = load_data()
    valid, errors, warnings = validation_summary(validation_data)
    if valid:
        st.success("Dataset validation passed.")
    for warning in warnings:
        st.warning(warning)
    for error in errors:
        st.error(error)

if st.button("Run Optimization", type="primary"):
    data = load_data()
    valid, errors, warnings = validation_summary(data)
    if not valid:
        st.error("Dataset validation failed.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()
    with st.spinner(f"Solving {model_name}..."):
        try:
            result, metrics, verification = run_selected_model(model_name, data)
        except Exception as exc:
            st.session_state.pop("optimization_metrics", None)
            st.session_state.pop("optimization_verification", None)
            st.session_state.pop("optimization_model_name", None)
            st.error(f"Optimization failed: {exc}")
        else:
            st.session_state["optimization_result"] = result
            st.session_state["optimization_metrics"] = metrics
            st.session_state["optimization_verification"] = verification
            st.session_state["optimization_model_name"] = model_name

if "optimization_metrics" in st.session_state:
    metrics = st.session_state["optimization_metrics"]
    verification = st.session_state["optimization_verification"]
    show_status(metrics["status"], "PASS" if verification["passed"] else "FAIL")
    emergency_demand = metrics["emergency_fulfillment_units"] + metrics["emergency_shortage_units"]
    normal_demand = metrics["normal_fulfillment_units"] + metrics["normal_shortage_units"]
    show_kpis({
        "Total fulfilled": metrics["total_supplied_units"],
        "Total unmet": metrics["total_unmet_units"],
        "Emergency fulfillment": f"{100 * metrics['emergency_fulfillment_units'] / emergency_demand:.1f}%",
        "Normal fulfillment": f"{100 * metrics['normal_fulfillment_units'] / normal_demand:.1f}%",
        "Transportation cost": f"INR {metrics['total_transportation_cost']:,.2f}",
        "Runtime": f"{metrics['runtime_seconds']:.4f}s",
    })
    if not metrics["is_optimal"]:
        st.warning("This solution is not confirmed optimal and must not be interpreted as optimal.")
    if not verification["passed"]:
        st.error("Independent verification failed.")
        for error in verification["errors"]:
            st.write(f"- {error}")
else:
    st.info("Select a model and click Run Optimization. Solving does not start automatically.")
