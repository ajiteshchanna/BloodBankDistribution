"""Integrated request-level transportation and assignment MILP."""

import pandas as pd

from src.models.assignment import build_assignment_model, run_assignment_model


def build_integrated_model(data: dict[str, pd.DataFrame] | None = None,
                           model_name: str = "integrated_milp"):
    """Build the integrated MILP.

    This implementation uses the assignment constraint structure and request-level
    shipment variables q[i,r], binary y[i,r], and unmet variables u[r].
    """
    model, context = build_assignment_model(data, model_name=model_name)
    return model, context


def run_integrated_model(data: dict[str, pd.DataFrame] | None = None,
                         time_limit: float | None = None,
                         output_flag: bool = False) -> dict:
    model, context = build_integrated_model(data)
    from src.optimization.solver import optimize_model
    from src.models.assignment import _assignment_result
    solver = optimize_model(model, time_limit=time_limit, output_flag=output_flag)
    return _assignment_result(model, context, solver)
