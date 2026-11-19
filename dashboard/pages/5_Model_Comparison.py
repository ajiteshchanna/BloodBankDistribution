"""Model comparison page."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.components.charts import comparison_chart
from dashboard.components.tables import show_table
from src.utils.config import RESULTS_DIR


st.title("Model Comparison")
path = RESULTS_DIR / "model_comparison.csv"
if not path.exists():
    st.info("Run model verification first to generate comparison results.")
    st.stop()

frame = pd.read_csv(path)
show_table(frame, "Verified model comparison")
for column, title, label in (
    ("total_fulfilled", "Total fulfilled units by model", "Units"),
    ("emergency_fulfilled", "Emergency fulfillment by model", "Units"),
    ("normal_fulfilled", "Normal fulfillment by model", "Units"),
    ("total_unmet", "Unmet demand by model", "Units"),
    ("transportation_cost", "Transportation cost by model", "INR"),
    ("solver_runtime", "Solver runtime by model", "Seconds"),
):
    comparison_chart(frame, column, title, label)

st.header("Interpretation")
st.write(
    "The Transportation LP uses aggregate demand and continuous shipments. The Assignment and "
    "Integrated MILPs retain request-level deadlines, integer quantities, and at-most-one-bank "
    "assignments. The current Assignment and Integrated formulations are mathematically equivalent; "
    "the LP is not universally superior because it solves a less restrictive problem."
)
