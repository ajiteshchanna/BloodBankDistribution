# Dashboard UI Guide

## Navigation

Run the application from the project root:

```bash
python -m streamlit run dashboard/app.py
```

Use the sidebar pages under Overview, Optimization, Analysis, and Project.

## Page purposes

- **Home:** dynamic project and dataset summary.
- **Dataset Overview:** tabbed source tables, inventory-demand charts, request filters, and routes.
- **Run Optimization:** validates data and runs one selected verified Gurobi model on demand.
- **Results:** displays the latest session result, allocation charts, request filters, and downloads.
- **Scenario Analysis:** reads generated Phase 5B scenario files without rerunning models.
- **Model Comparison:** reads verified model comparison output.
- **About:** explains the problem, formulations, assumptions, and limitations.

## Interpreting results

Emergency and normal fulfillment are reported separately. Transportation cost must be interpreted
alongside fulfillment because a lower cost can correspond to fewer supplied units. Solver status and
independent verification status are displayed separately.

## Downloads

Results and scenario pages provide CSV and JSON download buttons for the currently displayed data.

## Common errors

- If scenario files are missing, run `python -m scripts.run_scenarios`.
- If model execution fails, inspect the displayed solver status and error message.
- A non-OPTIMAL result must not be interpreted as a proven optimum.
- The dataset is synthetic academic data and the application is not a clinical decision-support tool.
