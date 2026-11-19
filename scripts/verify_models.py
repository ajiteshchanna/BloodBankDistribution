"""Run or rerun models and verify solutions independently."""

import sys

from src.analysis.comparison import (
    export_comparison,
    generate_verification_report,
)
from src.analysis.metrics import process_assignment_result, process_transportation_result
from src.analysis.verification import (
    verify_assignment_solution,
    verify_sequential_objectives,
    verify_transportation_solution,
)
from src.data.loader import load_all_datasets
from src.models.assignment import run_assignment_model
from src.models.integrated import run_integrated_model
from src.models.transportation import run_transportation_model


def main() -> int:
    data = load_all_datasets()
    results = {
        "transportation": run_transportation_model(data),
        "assignment": run_assignment_model(data),
        "integrated": run_integrated_model(data),
    }

    if not all(result["has_solution"] for result in results.values()):
        for name, result in results.items():
            print(f"{name}: {result['status']}")
        return 1

    metrics = {
        "transportation": process_transportation_result(results["transportation"]),
        "assignment": process_assignment_result(results["assignment"]),
        "integrated": process_assignment_result(results["integrated"]),
    }
    verification = {
        "transportation": verify_transportation_solution(
            data, results["transportation"], metrics["transportation"]
        ),
        "assignment": verify_assignment_solution(data, metrics["assignment"]),
        "integrated": verify_assignment_solution(data, metrics["integrated"]),
    }
    sequential = verify_sequential_objectives(data)

    from src.analysis.comparison import generate_comparison_rows
    rows = generate_comparison_rows(results, metrics, verification)
    export_comparison(rows)
    report_path = generate_verification_report(rows, verification, sequential)

    print("Model verification summary")
    for name in ("transportation", "assignment", "integrated"):
        status = "PASS" if verification[name]["passed"] else "FAIL"
        print(
            f"{name}: solver={results[name]['status']}, "
            f"verification={status}, cost={metrics[name]['total_transportation_cost']:.2f}"
        )
    print(f"Sequential objective verification: {'PASS' if sequential['passed'] else 'FAIL'}")
    print(f"Report: {report_path}")
    return 0 if all(item["passed"] for item in verification.values()) and sequential["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
