"""Independently verify optimization solution outputs against source datasets."""

from math import isclose

import pandas as pd

from gurobipy import GRB

from src.models.assignment import build_assignment_model, run_assignment_model
from src.models.transportation import build_transportation_model
from src.optimization.solver import safe_value


TOL = 1e-6


def _close(actual: float, expected: float, tolerance: float = TOL) -> bool:
    return isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def verify_inventory(data: dict[str, pd.DataFrame], shipments: dict[tuple[str, str, str], float]) -> dict:
    inventory = {
        (row.bank_id, row.blood_group): float(row.available_units)
        for row in data["inventory"].itertuples(index=False)
    }
    shipped = {}
    for (bank, blood_group), quantity in shipments.items():
        shipped[bank, blood_group] = shipped.get((bank, blood_group), 0.0) + quantity
    errors = []
    for key, quantity in shipped.items():
        available = inventory.get(key, 0.0)
        if quantity < -TOL:
            errors.append(f"Negative shipment for bank={key[0]}, group={key[1]}.")
        if quantity > available + TOL:
            errors.append(
                f"Inventory overuse for bank={key[0]}, group={key[1]}: "
                f"shipped={quantity}, available={available}."
            )
    for key in inventory:
        if key not in shipped:
            continue
    return {"passed": not errors, "errors": errors, "shipped_by_inventory_key": shipped}


def verify_request_assignments(data: dict[str, pd.DataFrame],
                               request_rows: list[dict]) -> dict:
    requests = data["requests"].set_index("request_id")
    errors = []
    for row in request_rows:
        rid = row["request_id"]
        if rid not in requests.index:
            errors.append(f"Unknown request ID: {rid}.")
            continue
        demand = float(requests.loc[rid, "required_units"])
        supplied = float(row.get("supplied_units", 0))
        unmet = float(row.get("unmet_units", 0))
        if supplied < -TOL or unmet < -TOL:
            errors.append(f"Negative quantity in request {rid}.")
        if abs(supplied - round(supplied)) > TOL:
            errors.append(f"Request {rid} has fractional MILP shipment {supplied}.")
        if abs(unmet - round(unmet)) > TOL:
            errors.append(f"Request {rid} has fractional unmet units {unmet}.")
        if supplied > demand + TOL:
            errors.append(f"Request {rid} receives {supplied} units above demand {demand}.")
        if not _close(supplied + unmet, demand):
            errors.append(
                f"Request {rid} balance is supplied={supplied}, unmet={unmet}, "
                f"demand={demand}."
            )
        assigned_bank = row.get("assigned_bank")
        if supplied > TOL and not assigned_bank:
            errors.append(f"Request {rid} has supplied units without an assigned bank.")
        if supplied <= TOL and assigned_bank:
            errors.append(f"Request {rid} has an assigned bank but no positive shipment.")

        hospital = requests.loc[rid, "hospital_id"]
        group = requests.loc[rid, "blood_group"]
        deadline = requests.loc[rid, "max_delivery_minutes"]
        if assigned_bank and supplied > TOL:
            transport = data["transport"]
            link = transport[
                (transport["bank_id"] == assigned_bank)
                & (transport["hospital_id"] == hospital)
            ]
            if link.empty or int(link.iloc[0]["available"]) != 1:
                errors.append(f"Request {rid} uses unavailable transport from {assigned_bank}.")
            elif pd.notna(deadline) and float(link.iloc[0]["delivery_time_minutes"]) > float(deadline):
                errors.append(f"Request {rid} misses its delivery deadline via {assigned_bank}.")

            inventory_row = data["inventory"][
                (data["inventory"]["bank_id"] == assigned_bank)
                & (data["inventory"]["blood_group"] == group)
            ]
            if inventory_row.empty:
                errors.append(f"Request {rid} uses invalid exact blood-group inventory.")
    return {"passed": not errors, "errors": errors}


def verify_transportation_cost(data: dict[str, pd.DataFrame],
                               bank_hospital_shipments: dict[tuple[str, str], float],
                               reported_cost: float) -> dict:
    transport = data["transport"].set_index(["bank_id", "hospital_id"])
    recalculated = 0.0
    errors = []
    for (bank, hospital), quantity in bank_hospital_shipments.items():
        try:
            cost = float(transport.loc[bank, hospital]["cost_per_unit_inr"])
        except (KeyError, TypeError):
            errors.append(f"Missing transport cost for {bank}->{hospital}.")
            continue
        recalculated += quantity * cost
    if abs(recalculated - reported_cost) > 1e-2:
        errors.append(
            f"Transportation cost mismatch: recalculated={recalculated:.2f}, "
            f"reported={reported_cost:.2f}."
        )
    return {"passed": not errors, "errors": errors, "recalculated_cost": recalculated}


def verify_shortages(data: dict[str, pd.DataFrame],
                     request_rows: list[dict]) -> dict:
    requests = data["requests"].set_index("request_id")
    emergency = 0.0
    normal = 0.0
    total_fulfilled = 0.0
    errors = []
    for row in request_rows:
        rid = row["request_id"]
        if rid not in requests.index:
            continue
        supplied = float(row["supplied_units"])
        unmet = float(row["unmet_units"])
        total_fulfilled += supplied
        if requests.loc[rid, "priority"] == "Emergency":
            emergency += unmet
        elif requests.loc[rid, "priority"] == "Normal":
            normal += unmet
    return {
        "passed": not errors,
        "errors": errors,
        "emergency_shortage": emergency,
        "normal_shortage": normal,
        "total_fulfilled": total_fulfilled,
    }


def verify_assignment_solution(data: dict[str, pd.DataFrame], metrics: dict) -> dict:
    request_rows = metrics.get("individual_request_assignments", [])
    inventory_shipments = {}
    bank_hospital = {}
    for row in request_rows:
        supplied = float(row["supplied_units"])
        if supplied <= TOL:
            continue
        rid = row["request_id"]
        request = data["requests"].set_index("request_id").loc[rid]
        bank = row["assigned_bank"]
        if bank:
            inventory_shipments[bank, request["blood_group"]] = (
                inventory_shipments.get((bank, request["blood_group"]), 0.0) + supplied
            )
            bank_hospital[bank, row["hospital_id"]] = (
                bank_hospital.get((bank, row["hospital_id"]), 0.0) + supplied
            )

    inventory_check = verify_inventory(data, inventory_shipments)
    request_check = verify_request_assignments(data, request_rows)
    cost_check = verify_transportation_cost(
        data, bank_hospital, float(metrics["total_transportation_cost"])
    )
    shortage_check = verify_shortages(data, request_rows)

    errors = (
        inventory_check["errors"]
        + request_check["errors"]
        + cost_check["errors"]
    )
    if metrics["status"] not in {"OPTIMAL", "TIME_LIMIT", "NODE_LIMIT", "INTERRUPTED", "SOLUTION_LIMIT"}:
        errors.append(f"Unusable reported solver status: {metrics['status']}.")
    if metrics["status"] != "OPTIMAL" and not metrics["is_optimal"]:
        errors.append("The result is not confirmed as optimal.")
    if not _close(shortage_check["emergency_shortage"], metrics["emergency_shortage_units"]):
        errors.append("Emergency shortage does not match independently calculated shortage.")
    if not _close(shortage_check["normal_shortage"], metrics["normal_shortage_units"]):
        errors.append("Normal shortage does not match independently calculated shortage.")
    if not _close(shortage_check["total_fulfilled"], metrics["total_supplied_units"]):
        errors.append("Total fulfilled units do not match individual shipments.")

    return {
        "passed": not errors,
        "errors": errors,
        "inventory": inventory_check,
        "requests": request_check,
        "cost": cost_check,
        "shortages": shortage_check,
    }


def verify_transportation_solution(data: dict[str, pd.DataFrame],
                                   result: dict,
                                   metrics: dict) -> dict:
    context = result["context"]
    inventory_shipments = {}
    bank_hospital = {}
    for (bank, hospital, group, category), variable in context["shipments"].items():
        quantity = safe_value(variable)
        if quantity > TOL:
            inventory_shipments[bank, group] = (
                inventory_shipments.get((bank, group), 0.0) + quantity
            )
            bank_hospital[bank, hospital] = (
                bank_hospital.get((bank, hospital), 0.0) + quantity
            )

    inventory_check = verify_inventory(data, inventory_shipments)
    cost_check = verify_transportation_cost(
        data, bank_hospital, float(metrics["total_transportation_cost"])
    )
    errors = inventory_check["errors"] + cost_check["errors"]
    if result["status"] != "OPTIMAL":
        errors.append(f"Transportation result status is {result['status']}, not OPTIMAL.")
    if not _close(sum(inventory_shipments.values()), metrics["total_supplied_units"], 1e-2):
        errors.append("Transportation total supplied units do not match extracted shipments.")
    if not _close(result["emergency_shortage"], metrics["emergency_shortage_units"], 1e-2):
        errors.append("Transportation emergency shortage does not match extracted shortage.")

    return {
        "passed": not errors,
        "errors": errors,
        "inventory": inventory_check,
        "cost": cost_check,
    }


def verify_sequential_objectives(data: dict[str, pd.DataFrame],
                                 time_limit: float | None = None) -> dict:
    """Compare hierarchical optimization with a sequential three-stage solve."""
    model, context = build_assignment_model(data, model_name="sequential_assignment_audit")
    model.Params.OutputFlag = 0
    if time_limit is not None:
        model.Params.TimeLimit = time_limit

    emergency_expr = sum(
        context["u"][rid] for rid in context["request_ids"]
        if context["requests_by_id"].loc[rid].priority == "Emergency"
    )
    normal_expr = sum(
        context["u"][rid] for rid in context["request_ids"]
        if context["requests_by_id"].loc[rid].priority == "Normal"
    )
    cost_expr = sum(
        float(context["links"][i, context["requests_by_id"].loc[rid].hospital_id].cost_per_unit_inr)
        * context["q"][i, rid]
        for i, rid in context["q"]
    )

    model.setObjective(emergency_expr, GRB.MINIMIZE)
    model.optimize()
    if model.Status != GRB.OPTIMAL:
        return {"passed": False, "errors": [f"Sequential emergency stage status: {model.Status}."]}
    emergency_opt = model.ObjVal
    model.addConstr(emergency_expr == emergency_opt, name="fix_verified_emergency_optimum")

    model.setObjective(normal_expr, GRB.MINIMIZE)
    model.optimize()
    if model.Status != GRB.OPTIMAL:
        return {"passed": False, "errors": [f"Sequential normal stage status: {model.Status}."]}
    normal_opt = model.ObjVal
    model.addConstr(normal_expr == normal_opt, name="fix_verified_normal_optimum")

    model.setObjective(cost_expr, GRB.MINIMIZE)
    model.optimize()
    if model.Status != GRB.OPTIMAL:
        return {"passed": False, "errors": [f"Sequential cost stage status: {model.Status}."]}

    existing = run_assignment_model(data, time_limit=time_limit)
    errors = []
    if not existing["is_optimal"]:
        errors.append(f"Existing assignment result is not optimal: {existing['status']}.")
    if not isclose(emergency_opt, existing["emergency_shortage"], rel_tol=1e-6, abs_tol=1e-6):
        errors.append("Emergency sequential optimum differs from multi-objective result.")
    if not isclose(normal_opt, existing["normal_shortage"], rel_tol=1e-6, abs_tol=1e-6):
        errors.append("Normal sequential optimum differs from multi-objective result.")
    if not isclose(model.ObjVal, existing["transportation_cost"], rel_tol=1e-5, abs_tol=1e-2):
        errors.append("Sequential cost differs from multi-objective cost.")
    return {
        "passed": not errors,
        "errors": errors,
        "emergency_shortage": emergency_opt,
        "normal_shortage": normal_opt,
        "transportation_cost": model.ObjVal,
    }
