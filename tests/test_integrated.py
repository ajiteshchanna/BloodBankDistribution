"""Tests for the integrated mixed-integer model."""

import pandas as pd

from src.models.integrated import run_integrated_model
from src.optimization.solver import safe_value


def integrated_data():
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
        "request_id": ["R1"],
        "hospital_id": ["H1"],
        "blood_group": ["O+"],
        "required_units": [8],
        "priority": ["Emergency"],
        "max_delivery_minutes": [180],
    })
    transport = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "hospital_id": ["H1", "H1"],
        "estimated_road_km": [20.0, 20.0],
        "delivery_time_minutes": [60.0, 60.0],
        "cost_per_unit_inr": [20.0, 20.0],
        "available": [1, 0],
    })
    return {
        "blood_banks": banks,
        "hospitals": hospitals,
        "inventory": inventory,
        "requests": requests,
        "transport": transport,
    }


def test_integrated_unavailable_connection_is_not_used():
    result = run_integrated_model(integrated_data())
    assert result["is_optimal"]
    assert result["total_supplied"] == 5
    assert ("B2", "R1") not in result["context"]["q"]


def test_integrated_assignment_and_shipment_are_consistent():
    result = run_integrated_model(integrated_data())
    for i, rid in result["context"]["q"]:
        quantity = safe_value(result["context"]["q"][i, rid])
        assignment = round(safe_value(result["context"]["y"][i, rid]))
        assert quantity <= int(result["context"]["requests_by_id"].loc[rid].required_units) * assignment
        assert assignment <= quantity


def test_integrated_request_balance_is_consistent():
    result = run_integrated_model(integrated_data())
    for rid in result["context"]["request_ids"]:
        supplied = sum(
            safe_value(result["context"]["q"][i, rid])
            for i in result["context"]["bank_ids"]
            if (i, rid) in result["context"]["q"]
        )
        unmet = safe_value(result["context"]["u"][rid])
        demand = int(result["context"]["requests_by_id"].loc[rid].required_units)
        assert round(supplied + unmet) == demand
