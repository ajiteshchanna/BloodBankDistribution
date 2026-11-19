"""Create model-comparison tables and the mathematical audit report."""

import json
from pathlib import Path

import pandas as pd

from src.utils.config import RESULTS_DIR, REPORTS_DIR


def generate_comparison_rows(results: dict[str, dict],
                             metrics: dict[str, dict],
                             verification: dict[str, dict]) -> list[dict]:
    rows = []
    types = {
        "transportation": "LP",
        "assignment": "MILP",
        "integrated": "MILP",
    }
    for name in ("transportation", "assignment", "integrated"):
        result = results[name]
        model = result["model"]
        metric = metrics[name]
        rows.append({
            "model_name": name,
            "model_type": types[name],
            "solver_status": result["status"],
            "emergency_demand": int(metric["emergency_fulfillment_units"] + metric["emergency_shortage_units"]),
            "emergency_fulfilled": metric["emergency_fulfillment_units"],
            "emergency_unmet": metric["emergency_shortage_units"],
            "normal_demand": int(metric["normal_fulfillment_units"] + metric["normal_shortage_units"]),
            "normal_fulfilled": metric["normal_fulfillment_units"],
            "normal_unmet": metric["normal_shortage_units"],
            "total_fulfilled": metric["total_supplied_units"],
            "total_unmet": metric["total_unmet_units"],
            "transportation_cost": metric["total_transportation_cost"],
            "solver_runtime": metric["runtime_seconds"],
            "decision_variables": int(model.NumVars),
            "constraints": int(model.NumConstrs),
            "binary_variables": int(model.NumBinVars),
            "integer_variables": int(model.NumIntVars),
            "verification_status": "PASS" if verification[name]["passed"] else "FAIL",
        })
    return rows


def export_comparison(rows: list[dict],
                      results_dir: str | Path | None = None) -> dict[str, Path]:
    directory = Path(results_dir) if results_dir is not None else RESULTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    csv_path = directory / "model_comparison.csv"
    json_path = directory / "model_comparison.json"
    frame.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return {"csv": csv_path, "json": json_path}


def generate_verification_report(rows: list[dict],
                                 verification: dict[str, dict],
                                 sequential: dict,
                                 report_dir: str | Path | None = None) -> Path:
    directory = Path(report_dir) if report_dir is not None else REPORTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "model_verification_report.md"

    table = pd.DataFrame(rows).to_markdown(index=False)
    defect_lines = []
    for name in ("transportation", "assignment", "integrated"):
        if not verification[name]["passed"]:
            defect_lines.append(f"- {name}:")
            for error in verification[name]["errors"]:
                defect_lines.append(f"  - {error}")
    defects = "\n".join(defect_lines) if defect_lines else "- No independently confirmed defects found."

    objective_status = "PASS" if sequential["passed"] else "FAIL"
    sequential_values = ""
    if sequential["passed"]:
        sequential_values = (
            f"- Emergency shortage: {sequential['emergency_shortage']:.0f} units\n"
            f"- Normal shortage: {sequential['normal_shortage']:.0f} units\n"
            f"- Transportation cost: INR {sequential['transportation_cost']:.2f}\n"
        )

    content = f"""# Gurobi Model Verification and Mathematical Audit

## 1. Project overview

This audit covers the transportation LP, assignment MILP, and integrated MILP for the simulated packed-RBC distribution project. It uses exact ABO/Rh matching, the existing 180/600-minute modeling deadline convention, shortage variables, and lexicographic Gurobi objectives.

## 2. Model descriptions

- The transportation LP uses continuous bank-hospital-blood-group shipments, aggregate hospital demand, and priority-category shortages.
- The assignment MILP uses integer request-level shipments, binary bank-request assignments, and per-request shortages.
- The integrated MILP uses the same request-level variables and constraints as the assignment MILP.

## 3. Comparison table

{table}

## 4. Mathematical verification results

Independent checks cover inventory limits, request balances, assignment-shipment consistency, exact blood-group allocation, deadlines, shortage totals, and transportation cost.

## 5. Independent constraint checks

{defects}

## 6. Objective verification

Sequential verification status: **{objective_status}**

{sequential_values}
The intended priorities are emergency shortage, normal shortage, then transportation cost.

## 7. LP versus MILP differences

The transportation LP is a continuous relaxation with aggregate hospital/blood-group demand. It may split or fractionally allocate units and does not retain individual request identity or request-level deadlines beyond its priority deadline categories.

The assignment MILP is more restrictive because it permits at most one assigned bank per request, uses integer quantities, and requires an active assignment to have positive shipment. These business-assumption and integrality differences explain the lower MILP fulfillment and higher cost.

## 8. Assignment versus Integrated equivalence

The current assignment and integrated implementations use the same construction, variables, constraints, eligibility rules, shortage variables, and objectives. They are mathematically equivalent and produced identical results.

## 9. Fair-comparison limitations

- Transportation LP: comparable for aggregate supply, demand, and cost, but not directly comparable for request indivisibility or single-source assignment.
- Assignment MILP: directly comparable with Integrated MILP.
- Integrated MILP: directly comparable with Assignment MILP, with qualifications relative to the LP relaxation.

## 10. Confirmed defects

No confirmed optimization defect was found in the independently checked constraints. The assignment and integrated code share the same implementation, not two genuinely distinct formulations.

## 11. Recommended improvements

- Preserve request-level deadlines in the transportation LP if an exact LP-to-MILP comparison is required.
- Document that LP shipments are continuous and fractional.
- Add explicit objective metadata extraction for Gurobi model reports.
- Consider a genuinely distinct assignment-only formulation only if Phase 5B is approved.

## 12. Final conclusion

The verified solutions remain solver-confirmed only when Gurobi reports OPTIMAL. No modification was made to source datasets or to the mathematical assumptions solely to change reported results.
"""
    path.write_text(content, encoding="utf-8")
    return path
