"""Dataset overview page using the actual project CSV files."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.common import load_data
from dashboard.components.charts import bar_chart, heatmap, stacked_fulfillment_chart
from dashboard.components.tables import show_table


st.title("Dataset Overview")
data = load_data()
inventory = data["inventory"]
requests = data["requests"]

show_table(data["blood_banks"], f"Blood Banks ({len(data['blood_banks'])})")
show_table(data["hospitals"], f"Hospitals ({len(data['hospitals'])})")
show_table(inventory, "Blood inventory")

inventory_group = inventory.groupby("blood_group", as_index=False)["available_units"].sum()
bar_chart(inventory_group, "blood_group", "available_units",
          "Available inventory by blood group", "Blood group", "Units")
inventory_bank = inventory.groupby("bank_id", as_index=False)["available_units"].sum()
bar_chart(inventory_bank, "bank_id", "available_units",
          "Available inventory by blood bank", "Blood bank", "Units")
inventory_heat = inventory.pivot(index="bank_id", columns="blood_group",
                                  values="available_units").fillna(0)
heatmap(inventory_heat, "Bank and blood-group inventory", "Blood group", "Blood bank")

st.subheader("Hospital requests")
show_table(requests, "Requests")
demand_priority = requests.groupby("priority", as_index=False)["required_units"].sum()
stacked_fulfillment_chart(
    demand_priority.rename(columns={"priority": "category", "required_units": "units"})
    .assign(status=lambda frame: frame["category"]),
    "Demand by priority",
)
demand_group = requests.groupby("blood_group", as_index=False)["required_units"].sum()
bar_chart(demand_group, "blood_group", "required_units",
          "Demand by blood group", "Blood group", "Units")
demand_hospital = requests.groupby("hospital_id", as_index=False)["required_units"].sum()
bar_chart(demand_hospital, "hospital_id", "required_units",
          "Demand by hospital", "Hospital", "Units")

comparison = inventory_group.merge(demand_group, on="blood_group", how="outer").fillna(0)
comparison = comparison.melt("blood_group", var_name="status", value_name="units")
comparison["status"] = comparison["status"].map({
    "available_units": "Available", "required_units": "Requested"
})
stacked_fulfillment_chart(comparison.rename(columns={"blood_group": "category"}),
                           "Inventory versus demand by blood group")

st.subheader("Transportation network")
transport = data["transport"]
selected_bank = st.multiselect("Filter banks", sorted(transport["bank_id"].unique()))
selected_hospital = st.multiselect("Filter hospitals", sorted(transport["hospital_id"].unique()))
filtered = transport.copy()
if selected_bank:
    filtered = filtered[filtered["bank_id"].isin(selected_bank)]
if selected_hospital:
    filtered = filtered[filtered["hospital_id"].isin(selected_hospital)]
show_table(filtered)
