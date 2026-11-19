"""Load and validate datasets, then write a JSON report."""

import sys

from src.data.loader import load_all_datasets
from src.data.validator import generate_validation_report, save_validation_report, validate_datasets
from src.utils.config import OUTPUTS_DIR


def main() -> int:
    try:
        data = load_all_datasets()
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"DATASET LOADING FAILED: {exc}")
        report = {
            "counts": {},
            "totals": {},
            "supply_demand_balance": {},
            "errors": [str(exc)],
            "warnings": [],
            "validation_status": "invalid",
        }
        report_path = OUTPUTS_DIR / "reports" / "dataset_validation.json"
        save_validation_report(report, report_path)
        print(f"Validation report saved to: {report_path}")
        return 1

    validation = validate_datasets(data)
    report = generate_validation_report(data, validation)
    report_path = save_validation_report(report, OUTPUTS_DIR / "reports" / "dataset_validation.json")

    print("Dataset Validation Summary")
    print("==========================")
    for name, count in report["counts"].items():
        print(f"{name}: {count}")
    for name, count in report["totals"].items():
        print(f"{name}: {count}")
    print(f"Validation status: {report['validation_status']}")

    if validation["errors"]:
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"- {error}")
    if validation["warnings"]:
        print("\nWarnings:")
        for warning in validation["warnings"]:
            print(f"- {warning}")

    print(f"\nValidation report saved to: {report_path}")
    return 1 if validation["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
