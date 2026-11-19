"""Display generated and verified Phase 5B scenario outputs."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.components.charts import comparison_chart, stacked_fulfillment_chart
from dashboard.components.tables import download_data, show_kpis, show_table
from src.utils.config import RESULTS_DIR


st.title("Scenario Analysis")
comparison_path = RESULTS_DIR / "scenario_comparison.csv"
json_path = RESULTS_DIR / "scenario_comparison.json"
if not comparison_path.exists() or not json_path.exists():
    st.info("Scenario results have not been generated. Run python -m scripts.run_scenarios to generate them.")
    st.stop()

comparison = pd.read_csv(comparison_path)
st.header("Scenario overview")
show_table(comparison[[
    "scenario_id", "name", "solver_status", "verification_status",
    "emergency_fulfilled", "normal_fulfilled", "total_fulfilled",
    "total_unmet", "transportation_cost",
]])

selected_id = st.selectbox("Select scenario", comparison["scenario_id"].tolist())
selected = comparison.loc[comparison["scenario_id"] == selected_id].iloc[0]
st.subheader(f"{selected['scenario_id']} — {selected['name']}")
st.write(selected["description"])
st.write(f"Modification: {selected.get('modifications', 'See scenario metadata.')}")
show_kpis({
    "Solver status": selected["solver_status"],
    "Verification": selected["verification_status"],
    "Emergency fulfilled": int(selected["emergency_fulfilled"]),
    "Emergency unmet": int(selected["emergency_unmet"]),
    "Normal fulfilled": int(selected["normal_fulfilled"]),
    "Total unmet": int(selected["total_unmet"]),
    "Cost (INR)": round(selected["transportation_cost"], 2),
})

st.header("Fulfillment comparison")
fulfillment = comparison.melt(
    id_vars=["scenario_id", "name"],
    value_vars=["emergency_fulfilled", "normal_fulfilled"],
    var_name="category", value_name="units",
)
fulfillment["category"] = fulfillment["category"].map({
    "emergency_fulfilled": "Emergency", "normal_fulfilled": "Normal"
})
fulfillment = fulfillment.rename(columns={"name": "scenario"})
comparison_chart(fulfillment.rename(columns={"scenario": "model_name"}), "units",
                 "Fulfilled units by scenario", "Units")

st.header("Unmet demand comparison")
unmet = comparison.melt(
    id_vars=["scenario_id", "name"],
    value_vars=["emergency_unmet", "normal_unmet", "total_unmet"],
    var_name="category", value_name="units",
).rename(columns={"name": "model_name"})
comparison_chart(unmet, "units", "Unmet demand by scenario", "Units")

st.header("Transportation cost comparison")
comparison_chart(comparison.rename(columns={"name": "model_name"}), "transportation_cost",
                 "Transportation cost by scenario", "INR")
st.caption("Cost must be interpreted alongside fulfillment; lower cost is not automatically better.")

st.header("Baseline versus selected scenario")
baseline = comparison.loc[comparison["scenario_id"] == "S1"].iloc[0]
delta = {
    "Emergency fulfilled change": int(selected["emergency_fulfilled"] - baseline["emergency_fulfilled"]),
    "Emergency unmet change": int(selected["emergency_unmet"] - baseline["emergency_unmet"]),
    "Normal fulfilled change": int(selected["normal_fulfilled"] - baseline["normal_fulfilled"]),
    "Total fulfilled change": int(selected["total_fulfilled"] - baseline["total_fulfilled"]),
    "Total unmet change": int(selected["total_unmet"] - baseline["total_unmet"]),
    "Cost change (INR)": round(selected["transportation_cost"] - baseline["transportation_cost"], 2),
}
show_kpis(delta)

st.header("Scenario insights")
if selected_id == "S1":
    st.write("The Base Case is the reference point for all scenario deltas.")
else:
    st.write(
        f"Compared with the Base Case, this scenario changes total fulfillment by "
        f"{delta['Total fulfilled change']} units and total unmet demand by "
        f"{delta['Total unmet change']} units."
    )

download_data("Download scenario comparison CSV", comparison, "scenario_comparison.csv")
download_data("Download scenario comparison JSON", json.loads(json_path.read_text(encoding="utf-8")),
              "scenario_comparison.json")
