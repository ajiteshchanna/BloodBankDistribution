"""Display the most recently solved and independently verified model."""

import pandas as pd
import streamlit as st

from dashboard.components.charts import bar_chart, heatmap, stacked_fulfillment_chart
from dashboard.components.tables import download_data, show_kpis, show_status, show_table


st.title("Optimization Results")
if "optimization_metrics" not in st.session_state:
    st.info("Run an optimization model first from the Run Optimization page.")
    st.stop()

metrics = st.session_state["optimization_metrics"]
model_name = st.session_state["optimization_model_name"]
verification = st.session_state["optimization_verification"]
st.caption(f"Most recent model: {model_name}")
emergency_demand = metrics["emergency_fulfillment_units"] + metrics["emergency_shortage_units"]
normal_demand = metrics["normal_fulfillment_units"] + metrics["normal_shortage_units"]
total_demand = emergency_demand + normal_demand
show_kpis({
    "Total fulfilled": f"{metrics['total_supplied_units']} / {total_demand}",
    "Overall fulfillment": f"{100 * metrics['total_supplied_units'] / total_demand:.1f}%",
    "Emergency demand": emergency_demand,
    "Emergency fulfilled": metrics["emergency_fulfillment_units"],
    "Normal demand": normal_demand,
    "Normal fulfilled": metrics["normal_fulfillment_units"],
    "Total unmet": metrics["total_unmet_units"],
    "Transport cost (INR)": f"{metrics['total_transportation_cost']:,.2f}",
    "Runtime (seconds)": f"{metrics['runtime_seconds']:.4f}",
})
st.progress(min(1.0, metrics["total_supplied_units"] / total_demand if total_demand else 0.0),
            text="Overall fulfillment")
show_status(metrics["status"], "PASS" if verification["passed"] else "FAIL")
st.caption(
    f"Emergency: {metrics['emergency_fulfillment_units']} / {emergency_demand} | "
    f"Normal: {metrics['normal_fulfillment_units']} / {normal_demand}"
)
fulfillment = pd.DataFrame([
    {"category": "Emergency", "status": "Fulfilled", "units": metrics["emergency_fulfillment_units"]},
    {"category": "Emergency", "status": "Unmet", "units": metrics["emergency_shortage_units"]},
    {"category": "Normal", "status": "Fulfilled", "units": metrics["normal_fulfillment_units"]},
    {"category": "Normal", "status": "Unmet", "units": metrics["normal_shortage_units"]},
])
stacked_fulfillment_chart(fulfillment, "Fulfilled versus unmet units")

utilization = pd.DataFrame.from_dict(metrics["bank_utilization"], orient="index").reset_index()
utilization = utilization.rename(columns={"index": "bank_id"})
bar_chart(utilization, "bank_id", "supplied_units", "Units supplied by blood bank", "Bank", "Units")

allocation = pd.DataFrame(metrics["bank_to_hospital_allocation"]).T
heatmap(allocation, "Bank-to-hospital allocation", "Hospital", "Blood bank")
hospital_totals = allocation.sum().rename_axis("hospital_id").reset_index(name="units")
bar_chart(hospital_totals, "hospital_id", "units", "Allocated units by hospital", "Hospital", "Units")

if "individual_request_assignments" in metrics:
    requests = pd.DataFrame(metrics["individual_request_assignments"])
    blood_group_totals = requests.groupby("blood_group", as_index=False)["supplied_units"].sum()
    bar_chart(blood_group_totals, "blood_group", "supplied_units",
              "Allocated units by blood group", "Blood group", "Units")
    st.subheader("Request allocations")
    group_filter = st.multiselect("Filter blood groups", sorted(requests["blood_group"].unique()))
    hospital_filter = st.multiselect("Filter hospitals", sorted(requests["hospital_id"].unique()))
    priority_filter = st.multiselect("Filter priorities", sorted(requests["priority"].unique()))
    filtered = requests.copy()
    if group_filter:
        filtered = filtered[filtered["blood_group"].isin(group_filter)]
    if hospital_filter:
        filtered = filtered[filtered["hospital_id"].isin(hospital_filter)]
    if priority_filter:
        filtered = filtered[filtered["priority"].isin(priority_filter)]
    show_table(filtered)
    download_data("Download request allocations", filtered, f"{model_name.lower().replace(' ', '_')}_requests.csv")

allocation_csv = allocation.reset_index(names="bank_id").melt(
    id_vars="bank_id", var_name="hospital_id", value_name="supplied_units"
)
download_data("Download allocation CSV", allocation_csv, f"{model_name.lower().replace(' ', '_')}_allocation.csv")
download_data("Download results JSON", metrics, f"{model_name.lower().replace(' ', '_')}_results.json")
