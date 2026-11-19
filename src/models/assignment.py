"""Request-level binary assignment MILP with partial fulfillment."""

import gurobipy as gp
import pandas as pd
from gurobipy import GRB

from src.data.loader import load_all_datasets
from src.optimization.solver import optimize_model, safe_value


def build_assignment_model(data: dict[str, pd.DataFrame] | None = None,
                           model_name: str = "assignment_milp") -> tuple[gp.Model, dict]:
    data = data or load_all_datasets()
    banks = data["blood_banks"]
    hospitals = data["hospitals"]
    inventory = data["inventory"]
    requests = data["requests"]
    transport = data["transport"]

    model = gp.Model(model_name)
    bank_ids = list(banks["bank_id"])
    request_ids = list(requests["request_id"])
    requests_by_id = requests.set_index("request_id")
    supply = {
        (row.bank_id, row.blood_group): int(row.available_units)
        for row in inventory.itertuples(index=False)
    }
    links = {
        (row.bank_id, row.hospital_id): row
        for row in transport.itertuples(index=False)
    }

    eligible = {}
    q = {}
    y = {}
    for i in bank_ids:
        for rid in request_ids:
            request = requests_by_id.loc[rid]
            link = links.get((i, request.hospital_id))
            is_eligible = (
                link is not None
                and int(link.available) == 1
                and float(link.delivery_time_minutes) <= float(request.max_delivery_minutes)
                and supply.get((i, request.blood_group), 0) > 0
            )
            if not is_eligible:
                continue
            eligible[i, rid] = True
            demand = int(request.required_units)
            y[i, rid] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{rid}")
            q[i, rid] = model.addVar(
                lb=0, ub=demand, vtype=GRB.INTEGER,
                name=f"q_{i}_{rid}",
            )
            model.addConstr(y[i, rid] <= q[i, rid], name=f"assignment_active_{i}_{rid}")
            model.addConstr(q[i, rid] <= demand * y[i, rid], name=f"assignment_link_{i}_{rid}")

    u = {}
    for rid in request_ids:
        demand = int(requests_by_id.loc[rid].required_units)
        u[rid] = model.addVar(lb=0, ub=demand, vtype=GRB.INTEGER, name=f"u_{rid}")
        model.addConstr(
            gp.quicksum(q[i, rid] for i in bank_ids if (i, rid) in q) + u[rid]
            == demand,
            name=f"demand_balance_{rid}",
        )
        model.addConstr(
            gp.quicksum(y[i, rid] for i in bank_ids if (i, rid) in y) <= 1,
            name=f"assignment_limit_{rid}",
        )

    for i in bank_ids:
        for g in set(requests["blood_group"]):
            model.addConstr(
                gp.quicksum(
                    q[i, rid]
                    for rid in request_ids
                    if (i, rid) in q
                    and requests_by_id.loc[rid].blood_group == g
                ) <= supply.get((i, g), 0),
                name=f"inventory_{i}_{g}",
            )

    emergency_expr = gp.quicksum(
        u[rid] for rid in request_ids
        if requests_by_id.loc[rid].priority == "Emergency"
    )
    normal_expr = gp.quicksum(
        u[rid] for rid in request_ids
        if requests_by_id.loc[rid].priority == "Normal"
    )
    cost_expr = gp.quicksum(
        float(links[i, requests_by_id.loc[rid].hospital_id].cost_per_unit_inr) * q[i, rid]
        for i, rid in q
    )
    model.setObjectiveN(emergency_expr, index=0, priority=3, weight=1.0, name="min_emergency_shortage")
    model.setObjectiveN(normal_expr, index=1, priority=2, weight=1.0, name="min_normal_shortage")
    model.setObjectiveN(cost_expr, index=2, priority=1, weight=1.0, name="min_transport_cost")
    model.ModelSense = GRB.MINIMIZE

    context = {
        "q": q, "y": y, "u": u, "eligible": eligible,
        "links": links, "bank_ids": bank_ids, "request_ids": request_ids,
        "requests": requests, "requests_by_id": requests_by_id, "data": data,
    }
    return model, context


def run_assignment_model(data: dict[str, pd.DataFrame] | None = None,
                         time_limit: float | None = None,
                         output_flag: bool = False) -> dict:
    model, context = build_assignment_model(data)
    solver = optimize_model(model, time_limit=time_limit, output_flag=output_flag)
    return _assignment_result(model, context, solver)


def _assignment_result(model, context, solver):
    q = context["q"]
    u = context["u"]
    requests = context["requests"]
    requests_by_id = context["requests_by_id"]
    shortage_by_priority = {
        priority: sum(
            safe_value(u[rid]) for rid in context["request_ids"]
            if requests_by_id.loc[rid].priority == priority
        )
        for priority in ("Emergency", "Normal")
    }
    cost = sum(
        float(context["links"][i, requests_by_id.loc[rid].hospital_id].cost_per_unit_inr)
        * safe_value(q[i, rid])
        for i, rid in q
    )
    emergency_demand = int(requests.loc[requests.priority == "Emergency", "required_units"].sum())
    normal_demand = int(requests.loc[requests.priority == "Normal", "required_units"].sum())
    return {
        **solver,
        "model": model,
        "context": context,
        "emergency_shortage": shortage_by_priority["Emergency"],
        "normal_shortage": shortage_by_priority["Normal"],
        "emergency_fulfillment": emergency_demand - shortage_by_priority["Emergency"],
        "normal_fulfillment": normal_demand - shortage_by_priority["Normal"],
        "total_supplied": sum(safe_value(v) for v in q.values()),
        "total_unmet": sum(safe_value(v) for v in u.values()),
        "transportation_cost": cost,
        "demand_units": int(requests["required_units"].sum()),
    }
