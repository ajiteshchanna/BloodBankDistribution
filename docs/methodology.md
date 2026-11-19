# Methodology

Phase 3 uses the existing synthetic datasets, validates their schemas and relationships, and documents the formulations before implementation.

Future phases may implement data loading, Gurobi models, lexicographic solver objectives, validation of model outputs, scenario analysis, and reporting. No optimization or dashboard implementation is included in this phase.

## Dashboard usage

Run `python -m streamlit run dashboard/app.py` from the project root. Use Dataset Overview for
source tables and charts, Run Optimization to select and execute one verified Gurobi model, Results
to inspect the retained session output and downloads, and Model Comparison to review the generated
comparison table. Scenario Analysis remains informational until Phase 5B outputs exist.

The dashboard uses the existing loaders, model runners, metrics, and independent verification
functions. It does not modify source CSV files or fabricate missing scenario results.
