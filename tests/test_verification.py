"""Tests for independent solution verification and audit comparisons."""

import pandas as pd

from src.analysis.verification import (
    verify_assignment_solution,
    verify_inventory,
    verify_request_assignments,
    verify_sequential_objectives,
    verify_transportation_cost,
)


def small_data():
    banks = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "bank_name": ["Bank 1", "Bank 2"],
        "city": ["City", "City"],
        "latitude_reference": [20.0, 20.0],
        "longitude_reference": [78.0, 78.0],
    })
    hospitals = pd.DataFrame({
        "hospital_id": ["H1"],
        "hospital_name": ["Hospital"],
        "city": ["City"],
        "latitude_reference": [20.0],
        "longitude_reference": [78.0],
    })
    inventory = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "blood_group": ["O+", "O+"],
        "available_units": [5, 5],
    })
    requests = pd.DataFrame({
        "request_id": ["R1", "R2"],
        "hospital_id": ["H1", "H1"],
        "blood_group": ["O+", "O+"],
        "required_units": [8, 4],
        "priority": ["Emergency", "Normal"],
        "max_delivery_minutes": [180, 600],
    })
    transport = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "hospital_id": ["H1", "H1"],
        "estimated_road_km": [20.0, 20.0],
        "delivery_time_minutes": [60.0, 60.0],
        "cost_per_unit_inr": [20.0, 30.0],
        "available": [1, 1],
    })
    return {
        "blood_banks": banks,
        "hospitals": hospitals,
        "inventory": inventory,
        "requests": requests,
        "transport": transport,
    }


def test_inventory_overuse_is_detected():
    check = verify_inventory(small_data(), {("B1", "O+"): 6.0})
    assert not check["passed"]
    assert any("Inventory overuse" in error for error in check["errors"])


def test_invalid_demand_balance_is_detected():
    row = [{
        "request_id": "R1", "supplied_units": 3,
        "unmet_units": 4, "assigned_bank": "B1", "hospital_id": "H1",
    }]
    check = verify_request_assignments(small_data(), row)
    assert not check["passed"]


def test_invalid_assignment_without_shipment_is_detected():
    row = [{
        "request_id": "R1", "supplied_units": 0,
        "unmet_units": 8, "assigned_bank": "B1", "hospital_id": "H1",
    }]
    check = verify_request_assignments(small_data(), row)
    assert not check["passed"]


def test_fractional_request_supplied_quantity_is_balance_valid_but_milp_requires_integrality():
    row = [{
        "request_id": "R1", "supplied_units": 3.5,
        "unmet_units": 4.5, "assigned_bank": "B1", "hospital_id": "H1",
    }]
    check = verify_request_assignments(small_data(), row)
    assert not check["passed"]
    assert any("fractional" in error.lower() for error in check["errors"])


def test_missed_delivery_deadline_is_detected():
    data = small_data()
    data["transport"].loc[0, "delivery_time_minutes"] = 200
    row = [{
        "request_id": "R1", "supplied_units": 2,
        "unmet_units": 6, "assigned_bank": "B1", "hospital_id": "H1",
    }]
    check = verify_request_assignments(data, row)
    assert not check["passed"]
    assert any("deadline" in error for error in check["errors"])


def test_incorrect_transportation_cost_is_detected():
    check = verify_transportation_cost(
        small_data(), {("B1", "H1"): 5.0}, reported_cost=99.0
    )
    assert not check["passed"]
    assert "cost mismatch" in " ".join(check["errors"]).lower()


def test_valid_partial_fulfillment_is_accepted():
    row = [{
        "request_id": "R1", "supplied_units": 5,
        "unmet_units": 3, "assigned_bank": "B1", "hospital_id": "H1",
    }]
    check = verify_request_assignments(small_data(), row)
    assert check["passed"]


def test_valid_zero_fulfillment_request_is_accepted():
    row = [{
        "request_id": "R1", "supplied_units": 0,
        "unmet_units": 8, "assigned_bank": None, "hospital_id": "H1",
    }]
    check = verify_request_assignments(small_data(), row)
    assert check["passed"]


def test_sequential_objective_audit_runs_for_full_dataset():
    check = verify_sequential_objectives({
        "blood_banks": small_data()["blood_banks"],
        "hospitals": small_data()["hospitals"],
        "inventory": small_data()["inventory"],
        "requests": small_data()["requests"],
        "transport": small_data()["transport"],
    })
    assert isinstance(check["passed"], bool)
