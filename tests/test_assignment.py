"""Tests for the assignment mixed-integer model."""

import pandas as pd

from src.models.assignment import build_assignment_model, run_assignment_model
from src.optimization.solver import safe_value


def assignment_data():
    banks = pd.DataFrame({
        "bank_id": ["B1"], "bank_name": ["Bank"],
        "city": ["City"], "latitude_reference": [20.0], "longitude_reference": [78.0],
    })
    hospitals = pd.DataFrame({
        "hospital_id": ["H1"], "hospital_name": ["Hospital"],
        "city": ["City"], "latitude_reference": [20.0], "longitude_reference": [78.0],
    })
    inventory = pd.DataFrame({
        "bank_id": ["B1"], "blood_group": ["O+"], "available_units": [6],
    })
    requests = pd.DataFrame({
        "request_id": ["R1", "R2"],
        "hospital_id": ["H1", "H1"],
        "blood_group": ["O+", "O+"],
        "required_units": [10, 10],
        "priority": ["Emergency", "Normal"],
        "max_delivery_minutes": [180, 600],
    })
    transport = pd.DataFrame({
        "bank_id": ["B1"], "hospital_id": ["H1"],
        "estimated_road_km": [20.0], "delivery_time_minutes": [60.0],
        "cost_per_unit_inr": [20.0], "available": [1],
    })
    return {
        "blood_banks": banks, "hospitals": hospitals,
        "inventory": inventory, "requests": requests, "transport": transport,
    }


def test_assignment_allows_partial_fulfillment():
    result = run_assignment_model(assignment_data())
    assert result["is_optimal"]
    assert result["total_supplied"] == 6
    assert result["total_unmet"] == 14
    assert result["emergency_shortage"] == 4
    assert result["normal_shortage"] == 10


def test_assignment_respects_inventory_conservation():
    result = run_assignment_model(assignment_data())
    shipped = sum(safe_value(v) for v in result["context"]["q"].values())
    assert shipped <= 6


def test_assignment_has_one_bank_request_link():
    result = run_assignment_model(assignment_data())
    for rid in result["context"]["request_ids"]:
        active = sum(
            round(safe_value(result["context"]["y"][i, rid]))
            for i in result["context"]["bank_ids"]
            if (i, rid) in result["context"]["y"]
        )
        assert active <= 1


def test_assignment_requires_positive_shipment_for_active_assignment():
    model, context = build_assignment_model(assignment_data())
    for i, rid in context["y"]:
        model.update()
        break
