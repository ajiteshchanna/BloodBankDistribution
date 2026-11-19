"""Validate schemas and relationships in the blood distribution datasets."""

import json
from pathlib import Path

import pandas as pd


BLOOD_GROUPS = {"O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"}
VALID_PRIORITIES = {"Emergency", "Normal"}
REQUIRED_COLUMNS = {
    "blood_banks": {"bank_id", "bank_name", "city", "latitude_reference", "longitude_reference"},
    "hospitals": {"hospital_id", "hospital_name", "city", "latitude_reference", "longitude_reference"},
    "inventory": {"bank_id", "blood_group", "available_units"},
    "requests": {"request_id", "hospital_id", "blood_group", "required_units", "priority", "max_delivery_minutes"},
    "transport": {"bank_id", "hospital_id", "estimated_road_km", "delivery_time_minutes", "cost_per_unit_inr", "available"},
}


def _empty_result():
    return {"errors": [], "warnings": []}


def _missing_columns(df, name):
    missing = sorted(REQUIRED_COLUMNS[name] - set(df.columns))
    return [f"{name}: missing required columns: {', '.join(missing)}"] if missing else []


def _is_whole_number(series):
    if not pd.api.types.is_numeric_dtype(series):
        return False
    nonnull = series.dropna()
    return bool((nonnull == nonnull.astype(int)).all())


def validate_blood_banks(df):
    result = _empty_result()
    result["errors"].extend(_missing_columns(df, "blood_banks"))
    if result["errors"]:
        return result
    if df["bank_id"].isna().any() or (df["bank_id"].astype(str).str.strip() == "").any():
        result["errors"].append("blood_banks: bank_id contains missing or empty values.")
    if df["bank_id"].duplicated().any():
        result["errors"].append("blood_banks: duplicate bank_id values found.")
    if df["bank_name"].isna().any() or (df["bank_name"].astype(str).str.strip() == "").any():
        result["errors"].append("blood_banks: bank_name contains missing or empty values.")
    if df["city"].isna().any() or (df["city"].astype(str).str.strip() == "").any():
        result["errors"].append("blood_banks: city contains missing or empty values.")
    for column, bounds in (
        ("latitude_reference", (-90, 90)),
        ("longitude_reference", (-180, 180)),
    ):
        if not pd.api.types.is_numeric_dtype(df[column]):
            result["errors"].append(f"blood_banks: {column} must be numeric.")
        elif df[column].dropna().between(*bounds).eq(False).any():
            result["errors"].append(f"blood_banks: {column} contains values outside {bounds}.")
    if df.duplicated().any():
        result["warnings"].append("blood_banks: duplicate records found.")
    return result


def validate_hospitals(df):
    result = _empty_result()
    result["errors"].extend(_missing_columns(df, "hospitals"))
    if result["errors"]:
        return result
    if df["hospital_id"].isna().any() or (df["hospital_id"].astype(str).str.strip() == "").any():
        result["errors"].append("hospitals: hospital_id contains missing or empty values.")
    if df["hospital_id"].duplicated().any():
        result["errors"].append("hospitals: duplicate hospital_id values found.")
    if df["hospital_name"].isna().any() or (df["hospital_name"].astype(str).str.strip() == "").any():
        result["errors"].append("hospitals: hospital_name contains missing or empty values.")
    if df["city"].isna().any() or (df["city"].astype(str).str.strip() == "").any():
        result["errors"].append("hospitals: city contains missing or empty values.")
    for column, bounds in (
        ("latitude_reference", (-90, 90)),
        ("longitude_reference", (-180, 180)),
    ):
        if not pd.api.types.is_numeric_dtype(df[column]):
            result["errors"].append(f"hospitals: {column} must be numeric.")
        elif df[column].dropna().between(*bounds).eq(False).any():
            result["errors"].append(f"hospitals: {column} contains values outside {bounds}.")
    if df.duplicated().any():
        result["warnings"].append("hospitals: duplicate records found.")
    return result


def validate_inventory(df, blood_banks=None):
    result = _empty_result()
    result["errors"].extend(_missing_columns(df, "inventory"))
    if result["errors"]:
        return result
    if df["blood_group"].isna().any() or (~df["blood_group"].isin(BLOOD_GROUPS)).any():
        result["errors"].append("inventory: contains missing or invalid blood_group values.")
    if df["available_units"].isna().any():
        result["errors"].append("inventory: available_units contains missing values.")
    elif not pd.api.types.is_numeric_dtype(df["available_units"]):
        result["errors"].append("inventory: available_units must be numeric.")
    elif not _is_whole_number(df["available_units"]):
        result["errors"].append("inventory: available_units must contain whole numbers.")
    elif (df["available_units"] < 0).any():
        result["errors"].append("inventory: available_units contains negative values.")
    if df.duplicated(["bank_id", "blood_group"]).any():
        result["errors"].append("inventory: duplicate bank_id and blood_group combinations found.")
    if blood_banks is not None and "bank_id" in blood_banks.columns:
        invalid = set(df["bank_id"].dropna()) - set(blood_banks["bank_id"].dropna())
        if invalid:
            result["errors"].append("inventory: invalid bank references: " + ", ".join(sorted(map(str, invalid))))
    return result


def validate_requests(df, hospitals=None):
    result = _empty_result()
    result["errors"].extend(_missing_columns(df, "requests"))
    if result["errors"]:
        return result
    if df["request_id"].isna().any() or (df["request_id"].astype(str).str.strip() == "").any():
        result["errors"].append("requests: request_id contains missing or empty values.")
    if df["request_id"].duplicated().any():
        result["errors"].append("requests: duplicate request_id values found.")
    if df["blood_group"].isna().any() or (~df["blood_group"].isin(BLOOD_GROUPS)).any():
        result["errors"].append("requests: contains missing or invalid blood_group values.")
    if df["required_units"].isna().any():
        result["errors"].append("requests: required_units contains missing values.")
    elif not pd.api.types.is_numeric_dtype(df["required_units"]):
        result["errors"].append("requests: required_units must be numeric.")
    elif not _is_whole_number(df["required_units"]):
        result["errors"].append("requests: required_units must contain whole numbers.")
    elif (df["required_units"] <= 0).any():
        result["errors"].append("requests: required_units must be positive.")
    if df["priority"].isna().any() or (~df["priority"].isin(VALID_PRIORITIES)).any():
        result["errors"].append("requests: priority must be Emergency or Normal.")
    deadlines = df["max_delivery_minutes"]
    if deadlines.notna().any():
        if not pd.api.types.is_numeric_dtype(deadlines):
            result["errors"].append("requests: max_delivery_minutes must be numeric.")
        elif (deadlines.dropna() < 0).any():
            result["errors"].append("requests: max_delivery_minutes contains negative values.")
    if hospitals is not None and "hospital_id" in hospitals.columns:
        invalid = set(df["hospital_id"].dropna()) - set(hospitals["hospital_id"].dropna())
        if invalid:
            result["errors"].append("requests: invalid hospital references: " + ", ".join(sorted(map(str, invalid))))
    if df.duplicated().any():
        result["warnings"].append("requests: duplicate records found.")
    return result


def validate_transport(df, blood_banks=None, hospitals=None):
    result = _empty_result()
    result["errors"].extend(_missing_columns(df, "transport"))
    if result["errors"]:
        return result
    if df.duplicated(["bank_id", "hospital_id"]).any():
        result["errors"].append("transport: duplicate bank_id and hospital_id connections found.")
    for column in ("estimated_road_km", "delivery_time_minutes", "cost_per_unit_inr"):
        if not pd.api.types.is_numeric_dtype(df[column]):
            result["errors"].append(f"transport: {column} must be numeric.")
        elif (df[column] < 0).any():
            result["errors"].append(f"transport: {column} contains negative values.")
    if df["available"].dropna().isin({0, 1}).eq(False).any():
        result["errors"].append("transport: available must contain only 0 or 1.")
    if blood_banks is not None and "bank_id" in blood_banks.columns:
        invalid = set(df["bank_id"].dropna()) - set(blood_banks["bank_id"].dropna())
        if invalid:
            result["errors"].append("transport: invalid bank references: " + ", ".join(sorted(map(str, invalid))))
    if hospitals is not None and "hospital_id" in hospitals.columns:
        invalid = set(df["hospital_id"].dropna()) - set(hospitals["hospital_id"].dropna())
        if invalid:
            result["errors"].append("transport: invalid hospital references: " + ", ".join(sorted(map(str, invalid))))
    return result


def validate_cross_dataset(data):
    result = _empty_result()
    required = ("blood_banks", "hospitals", "inventory", "requests", "transport")
    if any(name not in data for name in required):
        result["errors"].append("Cross-dataset validation requires all five datasets.")
        return result

    banks = data["blood_banks"]
    hospitals = data["hospitals"]
    inventory = data["inventory"]
    requests = data["requests"]
    transport = data["transport"]

    result["errors"].extend(validate_inventory(inventory, banks)["errors"])
    result["errors"].extend(validate_requests(requests, hospitals)["errors"])
    result["errors"].extend(validate_transport(transport, banks, hospitals)["errors"])

    supply = inventory.groupby("blood_group", dropna=False)["available_units"].sum(min_count=1)
    demand = requests.groupby("blood_group", dropna=False)["required_units"].sum(min_count=1)
    for group in sorted(BLOOD_GROUPS):
        available = float(supply.get(group, 0) or 0)
        required = float(demand.get(group, 0) or 0)
        if required > available:
            result["warnings"].append(
                f"Insufficient total inventory for {group}: available={int(available)}, requested={int(required)}."
            )

    if {"bank_id", "hospital_id", "delivery_time_minutes", "available"}.issubset(transport.columns):
        available_links = transport[transport["available"].fillna(0).astype(int) == 1]
        for _, request in requests.iterrows():
            deadline = request.get("max_delivery_minutes")
            eligible = available_links[available_links["hospital_id"] == request["hospital_id"]]
            if pd.notna(deadline):
                eligible = eligible[eligible["delivery_time_minutes"] <= deadline]
            exact_stock = inventory[
                (inventory["blood_group"] == request["blood_group"])
                & (inventory["available_units"] > 0)
                & (inventory["bank_id"].isin(set(eligible["bank_id"])))
            ]
            if exact_stock.empty:
                result["warnings"].append(
                    f"Request {request['request_id']} has no eligible source for exact blood-group matching."
                )

    expected = len(set(banks["bank_id"])) * len(set(hospitals["hospital_id"]))
    if len(transport) < expected:
        missing_count = expected - len(transport)
        result["warnings"].append(
            f"transport: missing {missing_count} expected bank-hospital connection(s); missing connections are unavailable."
        )
    return result


def validate_datasets(data):
    """Run schema and cross-dataset validation checks."""
    result = _empty_result()
    for name, validator in (
        ("blood_banks", validate_blood_banks),
        ("hospitals", validate_hospitals),
    ):
        if name not in data:
            result["errors"].append(f"{name}: dataset is missing.")
            continue
        part = validator(data[name])
        result["errors"].extend(part["errors"])
        result["warnings"].extend(part["warnings"])

    if "inventory" in data:
        part = validate_inventory(data["inventory"], data.get("blood_banks"))
        result["errors"].extend(part["errors"])
        result["warnings"].extend(part["warnings"])
    else:
        result["errors"].append("inventory: dataset is missing.")

    if "requests" in data:
        part = validate_requests(data["requests"], data.get("hospitals"))
        result["errors"].extend(part["errors"])
        result["warnings"].extend(part["warnings"])
    else:
        result["errors"].append("requests: dataset is missing.")

    if "transport" in data:
        part = validate_transport(data["transport"], data.get("blood_banks"), data.get("hospitals"))
        result["errors"].extend(part["errors"])
        result["warnings"].extend(part["warnings"])
    else:
        result["errors"].append("transport: dataset is missing.")

    if all(name in data for name in ("blood_banks", "hospitals", "inventory", "requests", "transport")):
        cross = validate_cross_dataset(data)
        result["errors"].extend(cross["errors"])
        result["warnings"].extend(cross["warnings"])
    return result


def generate_validation_report(data, validation=None):
    """Create the structured JSON-serializable dataset validation report."""
    banks = data.get("blood_banks")
    hospitals = data.get("hospitals")
    inventory = data.get("inventory")
    requests = data.get("requests")
    transport = data.get("transport")
    result = validation if validation is not None else validate_datasets(data)

    supply_by_group = (
        inventory.groupby("blood_group")["available_units"].sum().to_dict()
        if inventory is not None else {}
    )
    demand_by_group = (
        requests.groupby("blood_group")["required_units"].sum().to_dict()
        if requests is not None else {}
    )
    balance = {}
    for group in sorted(BLOOD_GROUPS):
        available = int(supply_by_group.get(group, 0))
        requested = int(demand_by_group.get(group, 0))
        balance[group] = {
            "available_units": available,
            "requested_units": requested,
            "balance_units": available - requested,
        }

    return {
        "counts": {
            "blood_banks": len(banks) if banks is not None else 0,
            "hospitals": len(hospitals) if hospitals is not None else 0,
            "blood_groups": len(BLOOD_GROUPS),
            "inventory_records": len(inventory) if inventory is not None else 0,
            "hospital_requests": len(requests) if requests is not None else 0,
            "transportation_records": len(transport) if transport is not None else 0,
        },
        "totals": {
            "available_blood_units": int(inventory["available_units"].sum()) if inventory is not None else 0,
            "requested_blood_units": int(requests["required_units"].sum()) if requests is not None else 0,
            "emergency_demand_units": int(requests.loc[requests["priority"] == "Emergency", "required_units"].sum()) if requests is not None else 0,
            "normal_demand_units": int(requests.loc[requests["priority"] == "Normal", "required_units"].sum()) if requests is not None else 0,
        },
        "supply_demand_balance": balance,
        "errors": result["errors"],
        "warnings": result["warnings"],
        "validation_status": "invalid" if result["errors"] else "valid",
    }


def save_validation_report(report, output_path):
    """Save a validation report as formatted JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


validate_data = validate_datasets
validate_all_datasets = validate_datasets
