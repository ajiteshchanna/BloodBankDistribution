# Viva Notes

## Key points

- The problem combines blood-bank supply, hospital requests, transport eligibility, shortages, and emergency prioritization.
- Exact ABO/Rh matching is used only as a simplified teaching model.
- The transportation LP uses continuous shipments.
- The integrated MILP uses integer request shipments and one binary assignment per bank-request pair.
- Shortages keep all shortage scenarios feasible.
- Gurobi lexicographic objectives prioritize emergency unmet units, then normal unmet units, then cost.

## Limitations

The data is synthetic, the coordinates are approximate, and the cost and travel parameters are illustrative. The model is not suitable for clinical or live operational use.
