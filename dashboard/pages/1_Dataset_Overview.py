"""Tabbed dataset overview using the actual project CSV files."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.common import load_data
from dashboard.components.charts import bar_chart, grouped_bar_chart, heatmap
from dashboard.components.tables import show_kpis, show_table


st.title("Dataset Overview")
data = load_data()
inventory = data["inventory"]
requests = data["requests"]
groups = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]

overview, banks_tab, hospitals_tab, transport_tab = st.tabs(
    ["Overview", "Blood Banks", "Hospitals & Requests", "Transportation Network"]
)
with overview:
    show_kpis({
        "Blood banks": len(data["blood_banks"]),
        "Hospitals": len(data["hospitals"]),
        "Available units": int(inventory["available_units"].sum()),
        "Requested units": int(requests["required_units"].sum()),
    })
    inventory_group = inventory.groupby("blood_group", as_index=False)["available_units"].sum()
    demand_group = requests.groupby("blood_group", as_index=False)["required_units"].sum()
    comparison = inventory_group.rename(columns={"available_units": "Available"}).merge(
        demand_group.rename(columns={"required_units": "Requested"}), on="blood_group", how="outer"
    ).fillna(0)
    grouped = comparison.melt("blood_group", var_name="measure", value_name="units")
    grouped_bar_chart(grouped, "blood_group", "units", "measure",
                      "Inventory versus demand", "Blood group", "Units")
    shortages = comparison[comparison["Available"] < comparison["Requested"]]
    if not shortages.empty:
        st.warning("Inventory shortage groups: " + ", ".join(shortages["blood_group"]))
    bar_chart(inventory_group, "blood_group", "available_units",
              "Available inventory by blood group", "Blood group", "Units")
with banks_tab:
    banks = data["blood_banks"]
    bank_filter = st.multiselect("Filter blood banks", sorted(banks["bank_id"].unique()))
    filtered_banks = banks[banks["bank_id"].isin(bank_filter)] if bank_filter else banks
    show_table(filtered_banks, "Blood-bank information")
    bank_inventory = inventory[inventory["bank_id"].isin(filtered_banks["bank_id"])]
    by_bank = bank_inventory.groupby("bank_id", as_index=False)["available_units"].sum()
    bar_chart(by_bank, "bank_id", "available_units", "Inventory by bank", "Bank", "Units")
    bank_heat = bank_inventory.pivot(index="bank_id", columns="blood_group",
                                     values="available_units").reindex(columns=groups).fillna(0)
    heatmap(bank_heat, "Bank by blood-group inventory", "Blood group", "Bank")
with hospitals_tab:
    show_table(data["hospitals"], "Hospital information")
    hospital_filter = st.multiselect("Filter hospitals", sorted(data["hospitals"]["hospital_id"].unique()))
    group_filter = st.multiselect("Filter blood groups", groups)
    priority_filter = st.multiselect("Filter priorities", ["Emergency", "Normal"])
    filtered = requests.copy()
    if hospital_filter:
        filtered = filtered[filtered["hospital_id"].isin(hospital_filter)]
    if group_filter:
        filtered = filtered[filtered["blood_group"].isin(group_filter)]
    if priority_filter:
        filtered = filtered[filtered["priority"].isin(priority_filter)]
    show_table(filtered, "Hospital requests")
    by_hospital = filtered.groupby("hospital_id", as_index=False)["required_units"].sum()
    bar_chart(by_hospital, "hospital_id", "required_units", "Demand by hospital", "Hospital", "Units")
    by_priority = filtered.groupby("priority", as_index=False)["required_units"].sum()
    bar_chart(by_priority, "priority", "required_units", "Demand by priority", "Priority", "Units")
with transport_tab:
    transport = data["transport"]
    bank_filter = st.multiselect("Route banks", sorted(transport["bank_id"].unique()))
    hospital_filter = st.multiselect("Route hospitals", sorted(transport["hospital_id"].unique()))
    filtered = transport.copy()
    if bank_filter:
        filtered = filtered[filtered["bank_id"].isin(bank_filter)]
    if hospital_filter:
        filtered = filtered[filtered["hospital_id"].isin(hospital_filter)]
    show_table(filtered, "Transportation routes")
