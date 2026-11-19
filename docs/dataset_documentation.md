# Dataset Documentation

## Provenance

The files are entirely synthetic teaching data generated on 2026-11-18 for an Operations Research case study. They do not represent actual blood bank inventory, hospital demand, road travel, or logistics rates. No external operational data source was used.

## Actual CSV schemas

### `blood_banks.csv`

| Column | Type | Meaning |
|---|---|---|
| `bank_id` | string | Unique blood-bank identifier |
| `bank_name` | string | Illustrative bank name |
| `city` | string | Illustrative city |
| `latitude_reference` | decimal degrees | Approximate reference coordinate |
| `longitude_reference` | decimal degrees | Approximate reference coordinate |

### `hospitals.csv`

| Column | Type | Meaning |
|---|---|---|
| `hospital_id` | string | Unique hospital identifier |
| `hospital_name` | string | Illustrative hospital name |
| `city` | string | Illustrative city |
| `latitude_reference` | decimal degrees | Approximate reference coordinate |
| `longitude_reference` | decimal degrees | Approximate reference coordinate |

### `inventory.csv`

`bank_id`, `blood_group`, and integer `available_units`. The key is bank plus blood group.

### `requests.csv`

`request_id`, `hospital_id`, exact `blood_group`, integer `required_units`, `priority` (`Emergency` or `Normal`), and optional integer `max_delivery_minutes`.

### `transport.csv`

`bank_id`, `hospital_id`, nonnegative `estimated_road_km`, nonnegative `delivery_time_minutes`, nonnegative `cost_per_unit_inr`, and `available` (`1` or `0`). The key is bank plus hospital.

## Units and conventions

- Inventory and demand quantities are units of packed red blood cells.
- Distances are estimated kilometres.
- Delivery times are minutes.
- Transportation costs are INR per unit.
- Blood groups are exactly `O+`, `O-`, `A+`, `A-`, `B+`, `B-`, `AB+`, and `AB-`.

## Validation rules

The validator checks identifiers, required values, ranges, duplicates, exact blood-group labels, integer quantities, numeric types, foreign keys, complete or explicitly unavailable corridors, exact per-group supply-demand balances, and request eligibility. Insufficient supply is a warning, not a critical error.

## Known limitations

City coordinates are approximate illustrative references. The transport estimates are synthetic and do not represent actual road routes or quotations. The data does not support clinical compatibility, expiry, crossmatching, or real emergency dispatch decisions.
