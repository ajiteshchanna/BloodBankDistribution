"""Tests for project dataset validation behavior."""

import pandas as pd

from src.data.validator import (
    generate_validation_report,
    validate_blood_banks,
    validate_cross_dataset,
    validate_hospitals,
    validate_inventory,
    validate_requests,
    validate_transport,
)


def valid_data():
    banks = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "bank_name": ["Bank 1", "Bank 2"],
        "city": ["City 1", "City 2"],
        "latitude_reference": [20.0, 21.0],
        "longitude_reference": [78.0, 79.0],
    })
    hospitals = pd.DataFrame({
        "hospital_id": ["H1"],
        "hospital_name": ["Hospital 1"],
        "city": ["City 1"],
        "latitude_reference": [20.0],
        "longitude_reference": [78.0],
    })
    inventory = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "blood_group": ["O+", "A+"],
        "available_units": [20, 10],
    })
    requests = pd.DataFrame({
        "request_id": ["R1", "R2"],
        "hospital_id": ["H1", "H1"],
        "blood_group": ["O+", "A+"],
        "required_units": [5, 5],
        "priority": ["Emergency", "Normal"],
        "max_delivery_minutes": [180, 600],
    })
    transport = pd.DataFrame({
        "bank_id": ["B1", "B2"],
        "hospital_id": ["H1", "H1"],
        "estimated_road_km": [20.0, 25.0],
        "delivery_time_minutes": [50, 60],
        "cost_per_unit_inr": [20.0, 22.0],
        "available": [1, 1],
    })
    return {
        "blood_banks": banks,
        "hospitals": hospitals,
        "inventory": inventory,
        "requests": requests,
        "transport": transport,
    }


def test_duplicate_bank_id_is_error():
    data = valid_data()
    data["blood_banks"] = pd.concat([data["blood_banks"], data["blood_banks"].iloc[[0]]], ignore_index=True)
    result = validate_blood_banks(data["blood_banks"])
    assert any("duplicate bank_id" in error for error in result["errors"])


def test_negative_inventory_is_error():
    data = valid_data()
    data["inventory"]["available_units"] = [-1, 10]
    result = validate_inventory(data["inventory"], data["blood_banks"])
    assert any("negative" in error for error in result["errors"])


def test_invalid_blood_group_is_error():
    data = valid_data()
    data["inventory"]["blood_group"] = ["O+", "C+"]
    result = validate_inventory(data["inventory"], data["blood_banks"])
    assert any("invalid blood_group" in error for error in result["errors"])


def test_invalid_priority_is_error():
    data = valid_data()
    data["requests"]["priority"] = ["Urgent", "Normal"]
    result = validate_requests(data["requests"], data["hospitals"])
    assert any("priority" in error for error in result["errors"])


def test_missing_transport_connection_is_warning():
    data = valid_data()
    data["transport"] = data["transport"].iloc[[0]]
    result = validate_cross_dataset(data)
    assert any("missing" in warning.lower() for warning in result["warnings"])


def test_insufficient_inventory_is_warning_not_error():
    data = valid_data()
    data["inventory"]["available_units"] = [1, 1]
    data["requests"]["required_units"] = [20, 20]
    result = validate_cross_dataset(data)
    assert not result["errors"]
    assert any("Insufficient total inventory" in warning for warning in result["warnings"])


def test_duplicate_hospital_id_is_error():
    data = valid_data()
    data["hospitals"] = pd.concat([data["hospitals"], data["hospitals"]], ignore_index=True)
    result = validate_hospitals(data["hospitals"])
    assert any("duplicate hospital_id" in error for error in result["errors"])


def test_duplicate_inventory_key_is_error():
    data = valid_data()
    data["inventory"] = pd.concat([data["inventory"], data["inventory"].iloc[[0]]], ignore_index=True)
    result = validate_inventory(data["inventory"], data["blood_banks"])
    assert any("duplicate bank_id" in error for error in result["errors"])


def test_validation_report_has_required_sections():
    data = valid_data()
    report = generate_validation_report(data)
    assert report["counts"]["blood_banks"] == 2
    assert report["totals"]["available_blood_units"] == 30
    assert report["totals"]["requested_blood_units"] == 10
    assert "supply_demand_balance" in report
