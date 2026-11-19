"""Tests for the transportation linear model."""

import pandas as pd

from src.models.transportation import build_transportation_model, run_transportation_model
from src.optimization.solver import safe_value


def small_data(available=5, transport_available=1):
    banks = pd.DataFrame({
        "bank_id": ["B1"],
        "bank_name": ["Bank 1"],
        "city": ["City"],
        "latitude_reference": [20.0],
        "longitude_reference": [78.0],
    })
    hospitals = pd.DataFrame({
        "hospital_id": ["H1"],
        "hospital_name": ["Hospital 1"],
        "city": ["City"],
        "latitude_reference": [20.0],
        "longitude_reference": [78.0],
    })
    inventory = pd.DataFrame({
        "bank_id": ["B1"],
        "blood_group": ["O+"],
        "available_units": [available],
    })
    requests = pd.DataFrame({
        "request_id": ["R1"],
        "hospital_id": ["H1"],
        "blood_group": ["O+"],
        "required_units": [10],
        "priority": ["Emergency"],
        "max_delivery_minutes": [180],
    })
    transport = pd.DataFrame({
        "bank_id": ["B1"],
        "hospital_id": ["H1"],
        "estimated_road_km": [20.0],
        "delivery_time_minutes": [60.0],
        "cost_per_unit_inr": [20.0],
        "available": [transport_available],
    })
    return {
        "blood_banks": banks,
        "hospitals": hospitals,
        "inventory": inventory,
        "requests": requests,
        "transport": transport,
    }


def test_transportation_honors_supply_shortage():
    result = run_transportation_model(small_data(available=5))
    assert result["is_optimal"]
    assert result["total_supplied"] == 5
    assert result["emergency_shortage"] == 5


def test_transportation_honors_unavailable_connection():
    result = run_transportation_model(small_data(available=5, transport_available=0))
    assert result["is_optimal"]
    assert result["total_supplied"] == 0
    assert result["emergency_shortage"] == 10


def test_transportation_objective_cost_is_nonnegative():
    result = run_transportation_model(small_data(available=5))
    assert result["transportation_cost"] >= 0
    assert result["transportation_cost"] == 100.0


def test_transportation_continuous_variables():
    model, context = build_transportation_model(small_data())
    for variable in context["shipments"].values():
        assert variable.vtype == "C"
