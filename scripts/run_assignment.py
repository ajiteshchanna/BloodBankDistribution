"""Run the assignment MILP and export its metrics."""

import sys

from src.analysis.metrics import export_metrics, process_assignment_result
from src.models.assignment import run_assignment_model


def main() -> int:
    result = run_assignment_model()
    if not result["has_solution"]:
        print(f"Assignment MILP status: {result['status']}")
        if result["solver_error"]:
            print(result["solver_error"])
        return 1

    metrics = process_assignment_result(result)
    exports = export_metrics(metrics, "assignment")
    print(f"Assignment MILP status: {result['status']}")
    print(f"Runtime: {result['runtime']:.6f} seconds")
    print(f"Emergency fulfilled: {metrics['emergency_fulfillment_units']}")
    print(f"Normal fulfilled: {metrics['normal_fulfillment_units']}")
    print(f"Total unmet: {metrics['total_unmet_units']}")
    print(f"Transportation cost: INR {metrics['total_transportation_cost']:.2f}")
    for path in exports.values():
        print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
