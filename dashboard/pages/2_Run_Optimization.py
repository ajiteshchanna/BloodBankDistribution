"""Run a selected verified Gurobi model on demand."""

import streamlit as st

from dashboard.common import load_data, run_selected_model, validation_summary


st.title("Run Optimization")
model_name = st.selectbox("Optimization model", [
    "Transportation LP", "Assignment MILP", "Integrated MILP",
])

if st.button("Run Optimization", type="primary"):
    data = load_data()
    valid, errors, warnings = validation_summary(data)
    if not valid:
        st.error("Dataset validation failed.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()
    for warning in warnings:
        st.warning(warning)

    with st.spinner(f"Solving {model_name}..."):
        try:
            result, metrics, verification = run_selected_model(model_name, data)
        except Exception as exc:
            st.error(f"Optimization failed: {exc}")
        else:
            st.session_state["optimization_result"] = result
            st.session_state["optimization_metrics"] = metrics
            st.session_state["optimization_verification"] = verification
            st.session_state["optimization_model_name"] = model_name

if "optimization_metrics" in st.session_state:
    metrics = st.session_state["optimization_metrics"]
    verification = st.session_state["optimization_verification"]
    st.success(f"{st.session_state['optimization_model_name']} completed.")
    cols = st.columns(4)
    cols[0].metric("Solver status", metrics["status"])
    cols[1].metric("Runtime (seconds)", metrics["runtime_seconds"])
    cols[2].metric("Total fulfilled", metrics["total_supplied_units"])
    cols[3].metric("Verification", "PASS" if verification["passed"] else "FAIL")
    if not metrics["is_optimal"]:
        st.warning("This solution is not confirmed optimal and must not be interpreted as optimal.")
    if not verification["passed"]:
        st.error("Independent verification failed.")
        for error in verification["errors"]:
            st.write(f"- {error}")
else:
    st.info("Select a model and click Run Optimization. Solving does not start automatically.")
