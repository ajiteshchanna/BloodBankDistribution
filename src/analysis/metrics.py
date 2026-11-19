"""Calculate, display, and export optimization result metrics."""

import json
from pathlib import Path

import pandas as pd

from src.optimization.solver import safe_value
from src.utils.config import RESULTS_DIR


def process_transportation_result(result: dict) -> dict:
    context = result["context"]
    data = context["data"]
    shipments = context["shipments"]
    bank_ids = context["bank_ids"]
    hospital_ids = context["hospital_ids"]

    allocation = pd.DataFrame(0.0, index=bank_ids, columns=hospital_ids)
    for (i, j, g, category), variable in shipments.items():
        allocation.loc[i, j] += safe_value(variable)

    bank_utilization = {}
    inventory = data["inventory"].set_index(["bank_id", "blood_group"])["available_units"]
    for i in bank_ids:
        supplied = float(allocation.loc[i].sum())
        available = float(inventory.loc[i].sum()) if i in inventory.index else 0.0
        bank_utilization[i] = {
            "available_units": int(available),
            "supplied_units": int(round(supplied)),
            "utilization_percent": round(100 * supplied / available, 2) if available else 0.0,
        }

    return _base_metrics(result, bank_utilization, allocation)


def process_assignment_result(result: dict) -> dict:
    context = result["context"]
    data = context["data"]
    bank_ids = context["bank_ids"]
    hospital_ids = list(data["hospitals"]["hospital_id"])
    allocation = pd.DataFrame(0.0, index=bank_ids, columns=hospital_ids)
    request_assignments = []

    for rid in context["request_ids"]:
        request = context["requests_by_id"].loc[rid]
        supplied = 0
        assigned_bank = None
        for i in bank_ids:
            key = (i, rid)
            if key not in context["q"]:
                continue
            units = round(safe_value(context["q"][key]))
            active = round(safe_value(context["y"][key]))
            if units > 0 and active == 1:
                assigned_bank = i
                supplied = units
                allocation.loc[i, request.hospital_id] += units
        unmet = round(safe_value(context["u"][rid]))
        request_assignments.append({
            "request_id": rid,
            "hospital_id": request.hospital_id,
            "blood_group": request.blood_group,
            "priority": request.priority,
            "requested_units": int(request.required_units),
            "supplied_units": supplied,
            "unmet_units": unmet,
            "assigned_bank": assigned_bank,
        })

    inventory = data["inventory"].set_index("bank_id")["available_units"].groupby(level=0).sum()
    bank_utilization = {}
    for i in bank_ids:
        supplied = float(allocation.loc[i].sum())
        available = float(inventory.get(i, 0))
        bank_utilization[i] = {
            "available_units": int(available),
            "supplied_units": int(round(supplied)),
            "utilization_percent": round(100 * supplied / available, 2) if available else 0.0,
        }

    metrics = _base_metrics(result, bank_utilization, allocation)
    metrics["individual_request_assignments"] = request_assignments
    return metrics


def _base_metrics(result: dict, bank_utilization: dict, allocation: pd.DataFrame) -> dict:
    return {
        "status": result["status"],
        "is_optimal": result["is_optimal"],
        "runtime_seconds": round(result["runtime"], 6),
        "total_available_inventory": int(result["context"]["data"]["inventory"]["available_units"].sum()),
        "total_supplied_units": int(round(result["total_supplied"])),
        "emergency_fulfillment_units": int(round(result["emergency_fulfillment"])),
        "normal_fulfillment_units": int(round(result["normal_fulfillment"])),
        "emergency_shortage_units": int(round(result["emergency_shortage"])),
        "normal_shortage_units": int(round(result["normal_shortage"])),
        "total_unmet_units": int(round(result["total_unmet"])),
        "total_transportation_cost": round(result["transportation_cost"], 2),
        "bank_utilization": bank_utilization,
        "bank_to_hospital_allocation": {
            bank: {hospital: int(round(units)) for hospital, units in row.items()}
            for bank, row in allocation.iterrows()
        },
    }


def export_metrics(metrics: dict, model_name: str, output_dir: str | Path | None = None) -> dict[str, Path]:
    """Export metrics to JSON and allocation/request CSV files."""
    directory = Path(output_dir) if output_dir is not None else RESULTS_DIR
    directory.mkdir(parents=True, exist_ok=True)

    json_path = directory / f"{model_name}_results.json"
    json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    allocation = metrics["bank_to_hospital_allocation"]
    allocation_rows = [
        {"bank_id": bank, "hospital_id": hospital, "supplied_units": units}
        for bank, hospitals in allocation.items()
        for hospital, units in hospitals.items()
    ]
    allocation_path = directory / f"{model_name}_allocation.csv"
    pd.DataFrame(allocation_rows).to_csv(allocation_path, index=False)

    exports = {"json": json_path, "allocation_csv": allocation_path}
    if "individual_request_assignments" in metrics:
        request_path = directory / f"{model_name}_requests.csv"
        pd.DataFrame(metrics["individual_request_assignments"]).to_csv(request_path, index=False)
        exports["requests_csv"] = request_path
    return exports
