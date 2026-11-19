"""Comprehensive academic and technical information about the project."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.common import load_data
from src.utils.config import RESULTS_DIR


st.title("About the Project")
st.caption("Academic Operations Research simulation")

data = load_data()
banks = data["blood_banks"]
hospitals = data["hospitals"]
inventory = data["inventory"]
requests = data["requests"]
transport = data["transport"]

available_units = int(inventory["available_units"].sum())
requested_units = int(requests["required_units"].sum())
emergency_units = int(
    requests.loc[requests["priority"] == "Emergency", "required_units"].sum()
)
normal_units = int(
    requests.loc[requests["priority"] == "Normal", "required_units"].sum()
)

overview_tab, models_tab, methodology_tab, results_tab, technical_tab = st.tabs(
    ["Overview", "Mathematical Models", "Methodology", "Results & Scenarios", "Technical Details"]
)

with overview_tab:
    st.subheader("Project introduction")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**What is blood bank distribution optimization?**")
            st.write(
                "It is the process of deciding how limited blood units should move from blood "
                "banks to hospitals while respecting inventory, exact blood-group matching, "
                "transport eligibility, delivery deadlines, and transportation cost."
            )
    with col2:
        with st.container(border=True):
            st.markdown("**Why Operations Research?**")
            st.write(
                "Operations Research provides mathematical models that make trade-offs explicit "
                "and find feasible allocations consistently. Emergency requests receive priority "
                "through a lexicographic objective, not an arbitrary penalty value."
            )

    st.subheader("Problem statement")
    with st.container(border=True):
        st.write(
            "Each blood bank holds a limited amount of each exact ABO/Rh blood group. "
            "Hospitals submit requests with required quantities, priorities, deadlines, and "
            "blood groups. The project determines which bank should supply each request, "
            "how many units should be supplied, and how shortages and transportation cost "
            "are affected."
        )

    st.subheader("Dataset")
    left, right = st.columns([1.5, 1])
    with left:
        show_data = pd.DataFrame(
            [
                ("Blood banks", len(banks)),
                ("Hospitals", len(hospitals)),
                ("Blood groups", inventory["blood_group"].nunique()),
                ("Hospital requests", len(requests)),
                ("Available units", available_units),
                ("Requested units", requested_units),
                ("Emergency demand units", emergency_units),
                ("Normal demand units", normal_units),
                ("Transportation routes", len(transport)),
            ],
            columns=["Measure", "Value"],
        )
        st.dataframe(show_data, width="stretch", hide_index=True)
    with right:
        with st.container(border=True):
            st.markdown("**Dataset files**")
            st.markdown(
                "- `blood_banks.csv`: bank identifiers and locations.\n"
                "- `hospitals.csv`: hospital identifiers and locations.\n"
                "- `inventory.csv`: bank inventory by exact blood group.\n"
                "- `requests.csv`: hospital demand, priority, and deadlines.\n"
                "- `transport.csv`: routes, delivery times, availability, and costs."
            )

    st.subheader("Objectives")
    with st.container(border=True):
        st.markdown(
            "The optimization uses Gurobi's lexicographic multi-objective hierarchy:\n\n"
            "1. **Minimize unmet emergency demand.**\n"
            "2. **Minimize unmet normal demand.**\n"
            "3. **Minimize transportation cost.**\n\n"
            "Each objective is solved in priority order, preserving the optimum of the "
            "higher-priority objective before proceeding to the next level."
        )

with models_tab:
    st.subheader("Transportation LP")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.latex(r"x_{ijg}\geq0")
        st.caption(
            "Continuous shipment quantity of blood group g from bank i to hospital j."
        )
    with c2:
        with st.container(border=True):
            st.markdown(
                "- Continuous, not integer, shipment quantities.\n"
                "- Aggregate demand by hospital and blood group.\n"
                "- Enforces bank inventory and available, timely transport links.\n"
                "- Provides a simplified baseline for comparison."
            )

    st.latex(r"\sum_j x_{ijg}\leq S_{ig}\qquad\forall i,g")
    st.caption("A bank cannot ship more than its available inventory for each exact blood group.")

    st.latex(r"\sum_i x_{ijg}+u_{jg}=D_{jg}\qquad\forall j,g")
    st.caption(
        "Hospital demand is fulfilled by shipments plus an aggregate shortage variable."
    )

    st.subheader("Assignment MILP")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.latex(r"y_{ir}\in\{0,1\}")
        st.latex(r"q_{ir}\in\mathbb Z_{\geq0}")
        st.caption(
            "y is binary assignment selection; q is the integer quantity supplied to request r."
        )
    with c2:
        with st.container(border=True):
            st.markdown(
                "- Integer supplied units.\n"
                "- Binary bank-to-request assignment decisions.\n"
                "- At most one supplying bank per request.\n"
                "- Exact matching and request-specific delivery eligibility.\n"
                "- Partial fulfillment is allowed when integer quantities are less than demand."
            )

    st.latex(r"\sum_i y_{ir}\leq1\qquad\forall r")
    st.caption("Each request may be assigned to at most one eligible bank.")

    st.latex(r"y_{ir}\leq q_{ir}\leq d_r y_{ir}\qquad\forall(i,r):e_{ir}=1")
    st.caption(
        "The assignment and shipment must agree: an active assignment requires at least "
        "one unit, and shipments cannot exceed the request demand."
    )

    st.subheader("Integrated MILP")
    st.latex(r"q_{ir}\in\mathbb Z_{\geq0},\qquad y_{ir}\in\{0,1\},\qquad u_r\in\mathbb Z_{\geq0}")
    st.caption(
        "q is the supplied quantity, y is the binary assignment, and u is unmet demand."
    )

    st.latex(r"\sum_i q_{ir}+u_r=d_r\qquad\forall r")
    st.caption("Every request is balanced between supplied units and explicit unmet units.")

    st.latex(r"\sum_{r:g(r)=g}q_{ir}\leq S_{ig}\qquad\forall i,g")
    st.caption("Total integer shipments conserve inventory independently for each bank and blood group.")

    st.latex(r"q_{ir}=y_{ir}=0\qquad\forall(i,r):e_{ir}=0")
    st.caption(
        "Ineligible pairs have no assignment or shipment. Eligibility requires exact blood-group "
        "matching, an available transport link, and a deadline-compatible delivery time."
    )

    st.latex(r"t_{i,h(r)}\leq T_r")
    st.caption("This delivery-time constraint is evaluated for each individual request.")

    st.subheader("Lexicographic objective hierarchy")
    st.latex(r"\min Z_1=\sum_{r\in R_E}u_r")
    st.caption("First minimize unmet emergency demand.")
    st.latex(r"\min Z_2=\sum_{r\in R_N}u_r")
    st.caption("With emergency unmet demand fixed at its optimum, minimize unmet normal demand.")
    st.latex(r"\min Z_3=\sum_{i,r}c_{i,h(r)}q_{ir}")
    st.caption("With both shortage objectives fixed, minimize transportation cost.")

    with st.expander("Assignment and Integrated equivalence"):
        st.write(
            "The current Assignment and Integrated implementations use the same request-level "
            "q, y, and u constraint structure. They therefore produce equivalent verified "
            "results in this project. The Assignment model name describes the binary "
            "request assignment behavior, while the Integrated model exposes the combined "
            "assignment and transportation formulation."
        )

with methodology_tab:
    st.subheader("Project workflow")
    workflow = pd.DataFrame(
        [
            ("1", "Dataset Loading", "`src/data/loader.py`", "Read CSV files for banks, hospitals, inventory, requests, and transport."),
            ("2", "Data Validation", "`src/data/validator.py`, `scripts/validate_data.py`", "Check required structures, quantities, exact matching, and eligibility warnings."),
            ("3", "Model Construction", "`src/models/`", "Construct LP or MILP variables, constraints, and lexicographic objectives."),
            ("4", "Gurobi Optimization", "`src/optimization/solver.py`", "Configure and solve the selected model while checking solver status and runtime."),
            ("5", "Independent Verification", "`src/analysis/verification.py`, `scripts/verify_models.py`", "Independently check inventory, balances, assignments, deadlines, costs, and objective consistency."),
            ("6", "Result Generation", "`src/analysis/metrics.py`", "Convert Gurobi output into fulfillment, unmet, cost, utilization, allocation, and request records."),
            ("7", "Scenario Analysis", "`src/analysis/scenarios.py`, `scripts/run_scenarios.py`", "Apply deterministic demand, inventory, and route disruptions to copies of the data."),
            ("8", "Dashboard Visualization", "`dashboard/`", "Present datasets, model execution, results, scenarios, and technical project information."),
        ],
        columns=["Step", "Stage", "Relevant code", "Purpose"],
    )
    st.dataframe(workflow, width="stretch", hide_index=True)

    st.subheader("How Gurobi determines the solution")
    with st.container(border=True):
        st.write(
            "Gurobi solves the LP or MILP using mathematical optimization algorithms. "
            "For the lexicographic objectives, each higher-priority objective is optimized "
            "first and only then is the next objective considered. A result is reported as "
            "optimal only when the solver status confirms optimality."
        )

    st.subheader("Independent verification")
    with st.container(border=True):
        st.write(
            "Independent verification does not trust a solver objective value alone. It "
            "reconstructs inventory use and demand balances from the reported solution, "
            "checks assignment consistency and eligible routes, recalculates transportation "
            "cost, and confirms the lexicographic objective sequence."
        )

with results_tab:
    st.subheader("Verified baseline model results")
    model_path = RESULTS_DIR / "model_comparison.csv"
    if model_path.exists():
        model_frame = pd.read_csv(model_path)
        display_models = model_frame[
            [
                "model_name",
                "solver_status",
                "emergency_fulfilled",
                "normal_fulfilled",
                "total_fulfilled",
                "total_unmet",
                "transportation_cost",
                "solver_runtime",
                "verification_status",
            ]
        ] if "model_name" in model_frame.columns else model_frame[
            [
                "model_name",
                "solver_status",
                "emergency_fulfilled",
                "normal_fulfilled",
                "total_fulfilled",
                "total_unmet",
                "transportation_cost",
                "solver_runtime",
                "verification_status",
            ]
        ]
        st.dataframe(display_models, width="stretch", hide_index=True)
    else:
        st.info("Verified model comparison results are unavailable.")

    with st.container(border=True):
        st.markdown(
            "**LP versus MILP interpretation:** the Transportation LP uses continuous aggregate "
            "shipments and does not enforce request-level single-bank assignment or exact "
            "request-level deadline representation. Therefore, it is a useful relaxed baseline "
            "but its lower cost does not establish that it is the better practical allocation."
        )

    st.subheader("Verified scenario analysis")
    scenario_path = RESULTS_DIR / "scenario_comparison.csv"
    if scenario_path.exists():
        scenario_frame = pd.read_csv(scenario_path)
        columns = [
            "scenario_id",
            "name",
            "solver_status",
            "verification_status",
            "emergency_fulfilled",
            "normal_fulfilled",
            "total_fulfilled",
            "total_unmet",
            "transportation_cost",
        ]
        st.dataframe(
            scenario_frame[[column for column in columns if column in scenario_frame]],
            width="stretch",
            hide_index=True,
        )

        scenario_descriptions = {
            "S1": "Base Case: original validated dataset.",
            "S2": "Emergency Surge: emergency request quantities increase by 25%, rounded upward per request.",
            "S3": "Inventory Shortage: every inventory record is reduced by 20%, floored and kept nonnegative.",
            "S4": "Transportation Disruption: the highest-allocation bank-hospital route is disabled.",
            "S5": "Targeted B+ Improvement: B+ inventory is increased by 20%, rounded upward per record.",
        }
        for scenario_id, description in scenario_descriptions.items():
            row = scenario_frame[scenario_frame["scenario_id"] == scenario_id]
            if not row.empty:
                values = row.iloc[0]
                with st.expander(f"{scenario_id}: {values['name']}"):
                    st.write(description)
                    st.write(
                        f"Fulfilled {int(values['total_fulfilled'])} units with "
                        f"{int(values['total_unmet'])} unmet; transportation cost "
                        f"INR {float(values['transportation_cost']):,.2f}. "
                        f"Solver: {values['solver_status']}; verification: "
                        f"{values['verification_status']}."
                    )
    else:
        st.info("Verified scenario comparison results are unavailable.")

with technical_tab:
    st.subheader("Technology stack")
    technology = pd.DataFrame(
        [
            ("Python", "Core implementation language."),
            ("Pandas", "CSV loading and tabular data processing."),
            ("NumPy", "Numerical utilities."),
            ("Gurobi / gurobipy", "LP and MILP construction and optimization."),
            ("Streamlit", "Interactive academic dashboard."),
            ("Plotly", "Interactive charts and allocation visualizations."),
            ("Matplotlib", "Supporting static scientific plots."),
            ("Pytest", "Automated regression and verification tests."),
        ],
        columns=["Component", "Role"],
    )
    st.dataframe(technology, width="stretch", hide_index=True)

    st.subheader("Project architecture")
    architecture = pd.DataFrame(
        [
            ("`dataset/`", "Source CSV datasets and dataset documentation."),
            ("`src/data/`", "CSV loading and data validation."),
            ("`src/models/`", "Transportation, assignment, and integrated model builders."),
            ("`src/optimization/`", "Gurobi solver configuration and objective utilities."),
            ("`src/analysis/`", "Metrics, verification, comparisons, and scenarios."),
            ("`dashboard/`", "Streamlit application, pages, and reusable components."),
            ("`scripts/`", "Command-line data, model, verification, and scenario runners."),
            ("`tests/`", "Pytest regression and solution-verification coverage."),
            ("`outputs/`", "Generated results, reports, and chart/report directories."),
            ("`docs/`", "Academic documentation, formulation, and project tracking."),
        ],
        columns=["Directory", "Purpose"],
    )
    st.dataframe(architecture, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Assumptions and limitations")
        with st.container(border=True):
            st.markdown(
                "- Synthetic academic dataset.\n"
                "- Exact ABO/Rh matching only.\n"
                "- No full clinical blood compatibility implementation.\n"
                "- No real-time hospital or inventory integration.\n"
                "- No patient-level clinical decision support.\n"
                "- No blood expiry or cold-chain handling.\n"
                "- Simplified transportation network.\n"
                "- Assignment and Integrated MILP are currently equivalent."
            )
    with right:
        st.subheader("Future scope")
        with st.container(border=True):
            st.markdown(
                "**Not implemented:**\n\n"
                "- Real-time inventory updates.\n"
                "- Blood expiry tracking.\n"
                "- Improved transportation time estimation.\n"
                "- Multi-period inventory planning.\n"
                "- Dynamic emergency demand forecasting.\n"
                "- Clinically validated compatibility and allocation logic, subject to medical oversight."
            )
