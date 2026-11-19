"""Deterministic scenario generation, execution, verification, and reporting."""

from copy import deepcopy
from math import ceil
from typing import Any

import pandas as pd

from src.analysis.metrics import process_assignment_result
from src.analysis.verification import verify_assignment_solution
from src.data.loader import load_all_datasets
from src.data.validator import validate_datasets
from src.models.integrated import run_integrated_model
from src.optimization.solver import safe_value


SCENARIOS = (
    ("S1", "Base Case"),
    ("S2", "Emergency Surge"),
    ("S3", "Inventory Shortage"),
    ("S4", "Transportation Disruption"),
    ("S5", "Targeted B+ Inventory Improvement"),
)


def _copy_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {name: frame.copy(deep=True) for name, frame in data.items()}


def _scenario_config(scenario_id: str) -> dict[str, Any]:
    return {
        "S1": {"scenario_id": "S1", "name": "Base Case", "description": "Original validated dataset."},
        "S2": {"scenario_id": "S2", "name": "Emergency Surge", "description": "Emergency request quantities increased by 25% using ceil per request."},
        "S3": {"scenario_id": "S3", "name": "Inventory Shortage", "description": "Every inventory record reduced by 20% using floor and nonnegative integer quantities."},
        "S4": {"scenario_id": "S4", "name": "Transportation Disruption", "description": "The highest baseline-allocation bank-hospital route is disabled."},
        "S5": {"scenario_id": "S5", "name": "Targeted B+ Inventory Improvement", "description": "B+ inventory increased by 20% using ceil per inventory record."},
    }[scenario_id]


def _baseline_route(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result = run_integrated_model(data)
    if not result["has_solution"]:
        raise RuntimeError(f"Cannot select disruption route: baseline status is {result['status']}.")
    totals: dict[tuple[str, str], float] = {}
    for (bank, request_id), variable in result["context"]["q"].items():
        quantity = safe_value(variable)
        if quantity:
            hospital = result["context"]["requests_by_id"].loc[request_id, "hospital_id"]
            totals[bank, hospital] = totals.get((bank, hospital), 0.0) + quantity
    if not totals:
        raise RuntimeError("Cannot select disruption route: baseline has no shipments.")
    bank, hospital = sorted(totals, key=lambda key: (-totals[key], key[0], key[1]))[0]
    return {
        "bank_id": bank,
        "hospital_id": hospital,
        "baseline_allocated_units": int(round(totals[bank, hospital])),
    }


def apply_scenario(data: dict[str, pd.DataFrame], scenario_id: str,
                   baseline_route: dict[str, Any] | None = None) -> tuple[dict[str, pd.DataFrame], dict]:
    """Return an independent modified dataset and exact modification metadata."""
    scenario = _copy_data(data)
    config = deepcopy(_scenario_config(scenario_id))
    if scenario_id == "S1":
        config["modifications"] = ["No dataset values changed."]
    elif scenario_id == "S2":
        mask = scenario["requests"]["priority"].eq("Emergency")
        before = scenario["requests"].loc[mask, "required_units"].astype(int)
        scenario["requests"].loc[mask, "required_units"] = before.map(lambda value: int(ceil(value * 1.25)))
        config["modified_requests"] = int(mask.sum())
        config["emergency_units_before"] = int(before.sum())
        config["emergency_units_after"] = int(scenario["requests"].loc[mask, "required_units"].sum())
        config["modifications"] = ["Emergency request required_units multiplied by 1.25 and rounded upward per request."]
    elif scenario_id == "S3":
        before = scenario["inventory"]["available_units"].astype(int)
        scenario["inventory"]["available_units"] = before.map(lambda value: max(0, int(value * 0.8)))
        config["inventory_units_before"] = int(before.sum())
        config["inventory_units_after"] = int(scenario["inventory"]["available_units"].sum())
        config["modifications"] = ["Every inventory available_units value multiplied by 0.8 and rounded downward."]
    elif scenario_id == "S4":
        route = baseline_route or _baseline_route(data)
        mask = (
            (scenario["transport"]["bank_id"] == route["bank_id"])
            & (scenario["transport"]["hospital_id"] == route["hospital_id"])
        )
        if not mask.any():
            raise ValueError(f"Baseline disruption route not found: {route}.")
        scenario["transport"].loc[mask, "available"] = 0
        affected = scenario["requests"]["hospital_id"].eq(route["hospital_id"]).sum()
        config["disabled_route"] = route
        config["affected_request_count"] = int(affected)
        config["modifications"] = [f"Set available=0 for {route['bank_id']}->{route['hospital_id']}."]
    elif scenario_id == "S5":
        mask = scenario["inventory"]["blood_group"].eq("B+")
        before = scenario["inventory"].loc[mask, "available_units"].astype(int)
        scenario["inventory"].loc[mask, "available_units"] = before.map(lambda value: int(ceil(value * 1.2)))
        config["b_plus_units_before"] = int(before.sum())
        config["b_plus_units_after"] = int(scenario["inventory"].loc[mask, "available_units"].sum())
        config["additional_b_plus_units"] = config["b_plus_units_after"] - config["b_plus_units_before"]
        config["modifications"] = ["B+ inventory available_units multiplied by 1.2 and rounded upward per record."]
    else:
        raise ValueError(f"Unknown scenario ID: {scenario_id}")
    return scenario, config


def _metric_record(config: dict, data: dict, result: dict, metrics: dict,
                   verification: dict, baseline: dict | None = None) -> dict:
    requests = data["requests"]
    available = int(data["inventory"]["available_units"].sum())
    emergency_demand = int(requests.loc[requests.priority == "Emergency", "required_units"].sum())
    normal_demand = int(requests.loc[requests.priority == "Normal", "required_units"].sum())
    record = {
        **config,
        "solver_status": result["status"],
        "verification_status": "PASS" if verification["passed"] else "FAIL",
        "verification_errors": verification["errors"],
        "available_inventory": available,
        "emergency_demand": emergency_demand,
        "normal_demand": normal_demand,
        "total_demand": emergency_demand + normal_demand,
        "emergency_fulfilled": metrics["emergency_fulfillment_units"],
        "normal_fulfilled": metrics["normal_fulfillment_units"],
        "total_fulfilled": metrics["total_supplied_units"],
        "emergency_unmet": metrics["emergency_shortage_units"],
        "normal_unmet": metrics["normal_shortage_units"],
        "total_unmet": metrics["total_unmet_units"],
        "emergency_fulfillment_percent": round(100 * metrics["emergency_fulfillment_units"] / emergency_demand, 4) if emergency_demand else 0.0,
        "normal_fulfillment_percent": round(100 * metrics["normal_fulfillment_units"] / normal_demand, 4) if normal_demand else 0.0,
        "overall_fulfillment_percent": round(100 * metrics["total_supplied_units"] / (emergency_demand + normal_demand), 4) if emergency_demand + normal_demand else 0.0,
        "transportation_cost": metrics["total_transportation_cost"],
        "solver_runtime_seconds": metrics["runtime_seconds"],
        "inventory_utilization_percent": round(100 * metrics["total_supplied_units"] / available, 4) if available else 0.0,
    }
    if baseline:
        for metric in ("emergency_fulfilled", "emergency_unmet", "normal_fulfilled", "total_fulfilled", "total_unmet", "transportation_cost"):
            base_value = baseline[metric]
            value = record[metric]
            record[f"{metric}_change"] = value - base_value
            record[f"{metric}_relative_change_percent"] = round(100 * (value - base_value) / base_value, 4) if base_value else None
    return record


def run_scenario(data: dict[str, pd.DataFrame], scenario_id: str,
                 baseline: dict | None = None,
                 baseline_route: dict[str, Any] | None = None) -> dict:
    modified, config = apply_scenario(data, scenario_id, baseline_route)
    validation = validate_datasets(modified)
    if validation["errors"]:
        return {
            "metrics": {**config, "solver_status": "INVALID_DATA", "verification_status": "FAIL",
                        "verification_errors": validation["errors"]},
            "allocation_rows": [], "request_rows": [], "data": modified,
        }
    result = run_integrated_model(modified)
    metrics = process_assignment_result(result)
    verification = verify_assignment_solution(modified, metrics)
    record = _metric_record(config, modified, result, metrics, verification, baseline)
    allocations = []
    for (bank, request_id), variable in result["context"]["q"].items():
        quantity = int(round(safe_value(variable)))
        if quantity:
            request = result["context"]["requests_by_id"].loc[request_id]
            allocations.append({
                "scenario_id": scenario_id, "bank_id": bank, "hospital_id": request.hospital_id,
                "blood_group": request.blood_group, "allocated_units": quantity,
            })
    requests = []
    for row in metrics["individual_request_assignments"]:
        requests.append({"scenario_id": scenario_id, **{key: row.get(key) for key in (
            "request_id", "priority", "requested_units", "supplied_units", "unmet_units", "assigned_bank"
        )}})
    return {"metrics": record, "allocation_rows": allocations, "request_rows": requests, "data": modified}


def run_all_scenarios(data: dict[str, pd.DataFrame] | None = None) -> dict:
    """Run all five deterministic scenarios and return structured results."""
    baseline_data = _copy_data(data or load_all_datasets())
    baseline_result = run_scenario(baseline_data, "S1")
    baseline_metrics = baseline_result["metrics"]
    route = _baseline_route(baseline_data)
    results = [baseline_result]
    for scenario_id, _ in SCENARIOS[1:]:
        results.append(run_scenario(baseline_data, scenario_id, baseline_metrics, route))
    return {
        "results": results,
        "comparison": [item["metrics"] for item in results],
        "allocations": [row for item in results for row in item["allocation_rows"]],
        "requests": [row for item in results for row in item["request_rows"]],
        "baseline_route": route,
    }
