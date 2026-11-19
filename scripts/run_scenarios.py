"""Execute and export the deterministic Phase 5B scenarios."""

import json
import sys

import pandas as pd

from src.analysis.scenarios import run_all_scenarios
from src.utils.config import REPORTS_DIR, RESULTS_DIR


def _report(comparison: list[dict]) -> str:
    frame = pd.DataFrame(comparison)
    table = frame[[
        "scenario_id", "name", "solver_status", "verification_status",
        "emergency_fulfilled", "normal_fulfilled", "total_fulfilled",
        "total_unmet", "transportation_cost",
    ]].to_markdown(index=False)
    return f"""# Scenario Analysis Report

## 1. Objective

Scenario analysis stress-tests the verified integrated MILP under deterministic changes to demand,
inventory, and network availability. It identifies sensitivity and resilience without changing the
lexicographic emergency-first objective.

## 2. Scenario definitions

{chr(10).join(f"- **{row['scenario_id']} — {row['name']}:** {row['description']} {row.get('modifications', [])}'" for row in comparison)}

## 3. Verified comparison

{table}

## 4. Emergency priority analysis

Emergency shortage remains the first optimization objective in every scenario. The computed
emergency fulfillment and unmet-demand values above are the results of the modified datasets, not
assumptions about how a scenario must behave.

## 5. Inventory sensitivity

The Inventory Shortage scenario reduces every inventory record. The targeted B+ improvement changes
only B+ records and tests whether the documented B+ shortage is supply-limited rather than
eligibility-limited.

## 6. Transportation resilience

The Transportation Disruption scenario disables the deterministic highest-allocation baseline
route. All other transport records remain available and the modified solution is independently
verified against the disabled route.

## 7. Cost analysis

Transportation cost is interpreted together with fulfillment and unmet demand. A lower cost is not
automatically better when fewer units are supplied.

## 8. Limitations

The data is synthetic academic data. The model uses exact ABO/Rh matching, no expiry or clinical
compatibility logic, no real-time hospital connectivity, a simplified transport network, and no
clinical decision-support capability.

## 9. Conclusions

The conclusions are limited to the computed scenario outputs above. Failed or unverified scenarios
are not presented as successful optimization results.
"""


def main() -> int:
    execution = run_all_scenarios()
    comparison = execution["comparison"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(comparison).to_csv(RESULTS_DIR / "scenario_comparison.csv", index=False)
    (RESULTS_DIR / "scenario_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    pd.DataFrame(execution["allocations"]).sort_values(
        ["scenario_id", "bank_id", "hospital_id", "blood_group"]
    ).to_csv(RESULTS_DIR / "scenario_allocations.csv", index=False)
    pd.DataFrame(execution["requests"]).sort_values(
        ["scenario_id", "request_id"]
    ).to_csv(RESULTS_DIR / "scenario_requests.csv", index=False)
    verification = {
        row["scenario_id"]: {
            "solver_status": row["solver_status"],
            "verification_status": row["verification_status"],
            "errors": row.get("verification_errors", []),
        }
        for row in comparison
    }
    (REPORTS_DIR / "scenario_verification.json").write_text(json.dumps({
        "baseline_route": execution["baseline_route"],
        "scenarios": verification,
    }, indent=2), encoding="utf-8")
    (REPORTS_DIR / "scenario_analysis_report.md").write_text(
        _report(comparison), encoding="utf-8"
    )
    for row in comparison:
        print(
            f"{row['scenario_id']} {row['name']}: "
            f"solver={row['solver_status']}, verification={row['verification_status']}, "
            f"fulfilled={row.get('total_fulfilled', 'n/a')}, unmet={row.get('total_unmet', 'n/a')}"
        )
    return 0 if all(row["verification_status"] == "PASS" for row in comparison) else 1


if __name__ == "__main__":
    sys.exit(main())
