"""Tests for deterministic scenario transformations and execution."""

import pandas as pd

from src.analysis.scenarios import apply_scenario, run_all_scenarios
from src.data.loader import load_all_datasets


def test_baseline_dataset_remains_unchanged():
    data = load_all_datasets()
    before = {name: frame.copy(deep=True) for name, frame in data.items()}
    apply_scenario(data, "S2")
    for name in data:
        pd.testing.assert_frame_equal(data[name], before[name])


def test_scenario_copies_are_independent():
    data = load_all_datasets()
    scenario, _ = apply_scenario(data, "S3")
    scenario["inventory"].loc[0, "available_units"] = 0
    assert scenario["inventory"].loc[0, "available_units"] != data["inventory"].loc[0, "available_units"]


def test_emergency_surge_modifies_only_emergency_demand():
    data = load_all_datasets()
    scenario, config = apply_scenario(data, "S2")
    assert scenario["requests"].loc[scenario["requests"].priority == "Normal", "required_units"].equals(
        data["requests"].loc[data["requests"].priority == "Normal", "required_units"]
    )
    assert config["emergency_units_after"] > config["emergency_units_before"]


def test_inventory_shortage_changes_only_inventory():
    data = load_all_datasets()
    scenario, config = apply_scenario(data, "S3")
    assert config["inventory_units_after"] < config["inventory_units_before"]
    pd.testing.assert_frame_equal(scenario["requests"], data["requests"])
    pd.testing.assert_frame_equal(scenario["transport"], data["transport"])


def test_disruption_disables_exactly_one_route():
    data = load_all_datasets()
    scenario, config = apply_scenario(data, "S4")
    route = config["disabled_route"]
    disabled = scenario["transport"].query("available == 0")
    assert len(disabled) == 1
    assert disabled.iloc[0]["bank_id"] == route["bank_id"]
    assert disabled.iloc[0]["hospital_id"] == route["hospital_id"]


def test_b_plus_improvement_changes_only_b_plus():
    data = load_all_datasets()
    scenario, config = apply_scenario(data, "S5")
    assert config["additional_b_plus_units"] > 0
    unchanged = data["inventory"]["blood_group"] != "B+"
    assert scenario["inventory"].loc[unchanged, "available_units"].equals(
        data["inventory"].loc[unchanged, "available_units"]
    )


def test_all_scenarios_have_verified_metrics_and_deterministic_values():
    first = run_all_scenarios()
    second = run_all_scenarios()
    assert [row["scenario_id"] for row in first["comparison"]] == ["S1", "S2", "S3", "S4", "S5"]
    assert all(row["solver_status"] == "OPTIMAL" for row in first["comparison"])
    assert all(row["verification_status"] == "PASS" for row in first["comparison"])
    fields = ("total_fulfilled", "total_unmet", "transportation_cost")
    assert [[row[field] for field in fields] for row in first["comparison"]] == [
        [row[field] for field in fields] for row in second["comparison"]
    ]


def test_scenario_integer_values_remain_nonnegative():
    data = load_all_datasets()
    for scenario_id in ("S1", "S2", "S3", "S4", "S5"):
        scenario, _ = apply_scenario(data, scenario_id)
        assert (scenario["inventory"]["available_units"] >= 0).all()
        assert (scenario["requests"]["required_units"] > 0).all()
        assert all(float(value).is_integer() for value in scenario["inventory"]["available_units"])
