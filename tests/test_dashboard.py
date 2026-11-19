"""Regression tests for dashboard data transformations and output loading."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_scenario_comparison_output_has_required_dashboard_columns():
    frame = pd.read_csv(ROOT / "outputs" / "results" / "scenario_comparison.csv")
    required = {
        "scenario_id", "name", "solver_status", "verification_status",
        "emergency_fulfilled", "normal_fulfilled", "total_fulfilled",
        "total_unmet", "transportation_cost",
    }
    assert required.issubset(frame.columns)
    assert frame["scenario_id"].tolist() == ["S1", "S2", "S3", "S4", "S5"]


def test_scenario_json_matches_csv_scenario_count():
    frame = pd.read_csv(ROOT / "outputs" / "results" / "scenario_comparison.csv")
    records = json.loads((ROOT / "outputs" / "results" / "scenario_comparison.json").read_text())
    assert len(records) == len(frame) == 5


def test_model_comparison_output_contains_verified_rows():
    frame = pd.read_csv(ROOT / "outputs" / "results" / "model_comparison.csv")
    assert set(frame["verification_status"]) == {"PASS"}
    assert set(frame["solver_status"]) == {"OPTIMAL"}


def test_about_page_uses_five_tabs_and_verified_sources():
    source = (ROOT / "dashboard" / "pages" / "6_About.py").read_text(encoding="utf-8")
    for label in (
        '"Overview"',
        '"Mathematical Models"',
        '"Methodology"',
        '"Results & Scenarios"',
        '"Technical Details"',
    ):
        assert label in source

    model_frame = pd.read_csv(ROOT / "outputs" / "results" / "model_comparison.csv")
    assert set(model_frame["model_name"]) == {
        "transportation",
        "assignment",
        "integrated",
    }

    scenario_frame = pd.read_csv(ROOT / "outputs" / "results" / "scenario_comparison.csv")
    assert scenario_frame["scenario_id"].tolist() == ["S1", "S2", "S3", "S4", "S5"]
