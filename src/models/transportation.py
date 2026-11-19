"""Transportation LP with aggregate hospital demand and priority-level shortages."""

from typing import Iterable

import gurobipy as gp
import pandas as pd
from gurobipy import GRB

from src.data.loader import load_all_datasets
from src.optimization.solver import optimize_model, safe_value


def build_transportation_model(data: dict[str, pd.DataFrame] | None = None,
                               model_name: str = "transportation_lp") -> tuple[gp.Model, dict]:
    """Build the continuous transportation LP.

    Request deadlines are aggregated by Emergency (180 minutes) and Normal
    (600 minutes) categories because this LP uses hospital-blood-group
    aggregates rather than request-level identities.
    """
    data = data or load_all_datasets()
    banks = data["blood_banks"]
    hospitals = data["hospitals"]
    inventory = data["inventory"]
    requests = data["requests"]
    transport = data["transport"]

    model = gp.Model(model_name)
    supply = {
        (row.bank_id, row.blood_group): int(row.available_units)
        for row in inventory.itertuples(index=False)
    }
    bank_ids = list(banks["bank_id"])
    hospital_ids = list(hospitals["hospital_id"])
    groups = sorted(set(requests["blood_group"]) | set(inventory["blood_group"]))

    emergency_demand = (
        requests[requests["priority"] == "Emergency"]
        .groupby(["hospital_id", "blood_group"])["required_units"].sum()
    )
    normal_demand = (
        requests[requests["priority"] == "Normal"]
        .groupby(["hospital_id", "blood_group"])["required_units"].sum()
    )

    links = {
        (row.bank_id, row.hospital_id): row
        for row in transport.itertuples(index=False)
    }
    shipments = {}
    for i in bank_ids:
        for j in hospital_ids:
            link = links.get((i, j))
            if link is None or int(link.available) != 1:
                continue
            for g in groups:
                for category, deadline in (("Emergency", 180), ("Normal", 600)):
                    if emergency_demand.get((j, g), 0) if category == "Emergency" else normal_demand.get((j, g), 0):
                        if float(link.delivery_time_minutes) <= deadline:
                            shipments[i, j, g, category] = model.addVar(
                                lb=0.0, vtype=GRB.CONTINUOUS,
                                name=f"x_{i}_{j}_{g}_{category}",
                            )

    emergency_shortage = {}
    normal_shortage = {}
    for (j, g), demand in emergency_demand.items():
        emergency_shortage[j, g] = model.addVar(
            lb=0.0, vtype=GRB.CONTINUOUS,
            name=f"u_emergency_{j}_{g}",
        )
    for (j, g), demand in normal_demand.items():
        normal_shortage[j, g] = model.addVar(
            lb=0.0, vtype=GRB.CONTINUOUS,
            name=f"u_normal_{j}_{g}",
        )

    model.update()
    for i in bank_ids:
        for g in groups:
            model.addConstr(
                gp.quicksum(
                    variable
                    for (bi, _, bg, _) , variable in shipments.items()
                    if bi == i and bg == g
                ) <= supply.get((i, g), 0),
                name=f"supply_{i}_{g}",
            )

    for (j, g), demand in emergency_demand.items():
        model.addConstr(
            gp.quicksum(
                variable
                for (i, hj, bg, category), variable in shipments.items()
                if hj == j and bg == g and category == "Emergency"
            ) + emergency_shortage[j, g] == float(demand),
            name=f"emergency_demand_{j}_{g}",
        )
    for (j, g), demand in normal_demand.items():
        model.addConstr(
            gp.quicksum(
                variable
                for (i, hj, bg, category), variable in shipments.items()
                if hj == j and bg == g and category == "Normal"
            ) + normal_shortage[j, g] == float(demand),
            name=f"normal_demand_{j}_{g}",
        )

    emergency_expr = gp.quicksum(emergency_shortage.values())
    normal_expr = gp.quicksum(normal_shortage.values())
    cost_expr = gp.quicksum(
        float(links[i, j].cost_per_unit_inr) * variable
        for (i, j, g, category), variable in shipments.items()
    )
    model.setObjectiveN(emergency_expr, index=0, priority=3, weight=1.0, name="min_emergency_shortage")
    model.setObjectiveN(normal_expr, index=1, priority=2, weight=1.0, name="min_normal_shortage")
    model.setObjectiveN(cost_expr, index=2, priority=1, weight=1.0, name="min_transport_cost")
    model.ModelSense = GRB.MINIMIZE

    context = {
        "shipments": shipments,
        "emergency_shortage": emergency_shortage,
        "normal_shortage": normal_shortage,
        "emergency_demand": emergency_demand,
        "normal_demand": normal_demand,
        "links": links,
        "groups": groups,
        "bank_ids": bank_ids,
        "hospital_ids": hospital_ids,
        "data": data,
    }
    return model, context


def run_transportation_model(data: dict[str, pd.DataFrame] | None = None,
                             time_limit: float | None = None,
                             output_flag: bool = False) -> dict:
    model, context = build_transportation_model(data)
    solver = optimize_model(model, time_limit=time_limit, output_flag=output_flag)

    emergency_shortage = sum(safe_value(v) for v in context["emergency_shortage"].values())
    normal_shortage = sum(safe_value(v) for v in context["normal_shortage"].values())
    cost = sum(
        float(context["links"][i, j].cost_per_unit_inr) * safe_value(v)
        for (i, j, g, category), v in context["shipments"].items()
    )
    demand = context["data"]["requests"]["required_units"].sum()
    result = {
        **solver,
        "model": model,
        "context": context,
        "emergency_shortage": emergency_shortage,
        "normal_shortage": normal_shortage,
        "emergency_fulfillment": float(context["data"]["requests"].loc[
            context["data"]["requests"]["priority"] == "Emergency", "required_units"
        ].sum()) - emergency_shortage,
        "normal_fulfillment": float(context["data"]["requests"].loc[
            context["data"]["requests"]["priority"] == "Normal", "required_units"
        ].sum()) - normal_shortage,
        "total_supplied": sum(safe_value(v) for v in context["shipments"].values()),
        "total_unmet": emergency_shortage + normal_shortage,
        "transportation_cost": cost,
        "demand_units": int(demand),
    }
    return result
