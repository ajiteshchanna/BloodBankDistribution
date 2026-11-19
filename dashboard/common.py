"""Shared dashboard loading and optimization helpers."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.metrics import process_assignment_result, process_transportation_result
from src.analysis.verification import verify_assignment_solution, verify_transportation_solution
from src.data.loader import load_all_datasets
from src.data.validator import validate_datasets
from src.models.assignment import run_assignment_model
from src.models.integrated import run_integrated_model
from src.models.transportation import run_transportation_model


@st.cache_data
def load_data():
    return load_all_datasets()


def run_selected_model(model_name: str, data: dict):
    runners = {
        "Transportation LP": run_transportation_model,
        "Assignment MILP": run_assignment_model,
        "Integrated MILP": run_integrated_model,
    }
    result = runners[model_name](data)
    if model_name == "Transportation LP":
        metrics = process_transportation_result(result)
        verification = verify_transportation_solution(data, result, metrics)
    else:
        metrics = process_assignment_result(result)
        verification = verify_assignment_solution(data, metrics)
    return result, metrics, verification


def validation_summary(data: dict) -> tuple[bool, list[str], list[str]]:
    validation = validate_datasets(data)
    return not validation["errors"], validation["errors"], validation["warnings"]
