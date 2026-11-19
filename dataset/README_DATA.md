# Phase 2 — Blood Bank Distribution OR Dataset

## Status and provenance
Generated 2026-11-18. Entirely **synthetic teaching data** created for an Operations Research case study; it does not represent actual blood bank inventory, hospital demand, travel times, service availability, or logistics rates. City coordinates are approximate reference coordinates, not verified facility coordinates. No external operational data source was accessed. Cite Python's standard-library `random` module for reproducible pseudorandom generation, and disclose AI assistance in dataset design.

**Not suitable for medical or emergency dispatch decisions.** This project models packed red blood cell (RBC) units and initially uses **exact ABO/Rh group matching only**, not clinical compatibility, crossmatching, component-specific guidance, expiry, or patient-level clinical judgment.

## Files and columns
- `blood_banks.csv`: `bank_id` (PK), `bank_name`, `city`, `latitude_reference`, `longitude_reference`.
- `hospitals.csv`: `hospital_id` (PK), `hospital_name`, `city`, `latitude_reference`, `longitude_reference`.
- `inventory.csv`: `bank_id` (FK), `blood_group`, `available_units` (integer). Unique key: bank + blood group.
- `requests.csv`: `request_id` (PK), `hospital_id` (FK), `blood_group`, `required_units` (integer), `priority` (Emergency/Normal), `max_delivery_minutes`.
- `transport.csv`: `bank_id` (FK), `hospital_id` (FK), `estimated_road_km`, `delivery_time_minutes`, `cost_per_unit_inr`, `available` (1/0). Unique key: bank + hospital.
- `dataset_summary.json`: row counts and demand/supply totals.

## Data-generation assumptions
1. Five fictional blood banks and eight fictional hospitals are situated in real Maharashtra cities; facility names are illustrative.
2. Each bank has stock for all eight ABO/Rh groups. Quantities are deterministic synthetic integers produced with random seed 20261118.
3. There are four requests per hospital (32 total); two are emergency and two normal. Each request is for a single blood group.
4. Emergency requests have 180-minute maximum delivery time; normal requests have 600 minutes. These are **modeling thresholds**, not clinical standards.
5. All 40 bank-to-hospital corridors are assumed available. Estimated road distance = max(8, 1.25 × great-circle distance + 8), rounded to km. This is **not actual road routing**.
6. Estimated delivery time = 25 + road_distance/45 × 60, rounded to minutes. This is a synthetic logistics estimate.
7. Cost per unit in INR = 12 + 0.38 × road_distance. This is an illustrative **variable allocation cost**, not a real transport quotation. It ignores fixed dispatch costs; add these only with a separate decision variable and cost field.
8. Shipment quantities must be nonnegative integers. A request may be fulfilled by one bank only if that bank is eligible within its delivery limit; the model may use a binary assignment variable and an unmet-demand variable.
9. Prioritize minimizing emergency unmet units, then normal unmet units, then total transport cost (lexicographic objectives). Avoid optimizing only cost with optional demand.
10. Total stock across groups is not interchangeable: each blood group has its own supply and demand. A total stock surplus does not guarantee all requests can be fulfilled.

## Model design warning
A single-bank-per-request assignment can create unavoidable shortages even when aggregate group supply is adequate. For partially fulfilled requests, explicitly define whether partial deliveries are allowed. Suggested initial rule: each request can receive units from at most one bank, and unfulfilled units are recorded. Do not interpret assignment as successful fulfillment without shipment-linking constraints.

## Suggested validation
Verify unique IDs, foreign keys, group labels, nonnegative integer stock/demand, positive costs, 40 complete corridors, request eligibility by delivery limit, and exact per-group inventory/demand balances. Test infeasible/shortage scenarios intentionally and verify the solver status before reading decision values.

## Source/access-date disclosure for report
- Dataset origin: AI-assisted, deterministic synthetic scenario generated 2026-11-18.
- External operational sources: none used; access date not applicable.
- Geographical city labels and approximate coordinates: illustrative references, not sourced/verified for a real deployment.
- Optimization implementation (Phase 3 onward): cite Gurobi documentation and Python/Pandas versions actually used, with access dates when consulted.
