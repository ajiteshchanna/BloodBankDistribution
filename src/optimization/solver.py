"""Configure, execute, and summarize Gurobi optimization runs."""

import time
from typing import Any

import gurobipy as gp
from gurobipy import GRB


STATUS_NAMES = {
    GRB.LOADED: "LOADED",
    GRB.OPTIMAL: "OPTIMAL",
    GRB.INFEASIBLE: "INFEASIBLE",
    GRB.INF_OR_UNBD: "INFEASIBLE_OR_UNBOUNDED",
    GRB.UNBOUNDED: "UNBOUNDED",
    GRB.CUTOFF: "CUTOFF",
    GRB.INTERRUPTED: "INTERRUPTED",
    GRB.NODE_LIMIT: "NODE_LIMIT",
    GRB.TIME_LIMIT: "TIME_LIMIT",
    GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
    GRB.NUMERIC: "NUMERIC",
}


def configure_model(model: gp.Model, time_limit: float | None = None,
                    output_flag: bool = False) -> gp.Model:
    """Apply standard solver settings without hiding infeasible conditions."""
    model.Params.OutputFlag = 1 if output_flag else 0
    model.Params.MIPGap = 0.0
    if time_limit is not None:
        if time_limit <= 0:
            raise ValueError("time_limit must be positive.")
        model.Params.TimeLimit = float(time_limit)
    return model


def optimize_model(model: gp.Model, time_limit: float | None = None,
                   output_flag: bool = False) -> dict[str, Any]:
    """Optimize a model and return runtime, status, and solution availability."""
    configure_model(model, time_limit=time_limit, output_flag=output_flag)
    started = time.perf_counter()
    try:
        model.optimize()
    except gp.GurobiError as exc:
        elapsed = time.perf_counter() - started
        return {
            "status_code": getattr(model, "Status", None),
            "status": STATUS_NAMES.get(getattr(model, "Status", None), "SOLVER_ERROR"),
            "runtime": elapsed,
            "solver_error": str(exc),
            "has_solution": False,
            "is_optimal": False,
        }
    elapsed = time.perf_counter() - started
    status_code = model.Status
    has_solution = status_code in (GRB.OPTIMAL,) or (
        status_code in (GRB.TIME_LIMIT, GRB.INTERRUPTED, GRB.NODE_LIMIT, GRB.SOLUTION_LIMIT)
        and model.SolCount > 0
    )
    return {
        "status_code": status_code,
        "status": STATUS_NAMES.get(status_code, str(status_code)),
        "runtime": elapsed,
        "solver_error": None,
        "has_solution": has_solution,
        "is_optimal": status_code == GRB.OPTIMAL,
    }


def safe_value(variable: gp.Var) -> float:
    """Read a solution value only when Gurobi can provide one."""
    try:
        return float(variable.X)
    except (AttributeError, gp.GurobiError):
        return 0.0


def objective_value(model: gp.Model) -> float | None:
    """Return the final objective value only for a model with a solution."""
    if model.SolCount == 0:
        return None
    return float(model.ObjVal)
