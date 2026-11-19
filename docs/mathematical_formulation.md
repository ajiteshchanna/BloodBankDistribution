# Mathematical Formulation

## Sets

- \(B\): blood banks, indexed by \(i\).
- \(H\): hospitals, indexed by \(j\).
- \(G\): exact ABO/Rh blood groups, indexed by \(g\).
- \(R\): hospital requests, indexed by \(r\).
- \(R_E\): emergency requests.
- \(R_N\): normal requests.

## Parameters

- \(S_{ig}\): available units of group \(g\) at bank \(i\).
- \(d_r\): units requested by request \(r\).
- \(h(r)\): hospital associated with request \(r\).
- \(g(r)\): blood group associated with request \(r\).
- \(c_{ij}\): transportation cost per unit from bank \(i\) to hospital \(j\), in INR.
- \(t_{ij}\): estimated delivery time from bank \(i\) to hospital \(j\), in minutes.
- \(T_r\): maximum allowed delivery time for request \(r\), when provided.
- \(e_{ir}\): 1 if bank \(i\) can serve request \(r\), otherwise 0.

Eligibility \(e_{ir}=1\) requires exact blood-group matching, an available bank-hospital transport link, and either no deadline or \(t_{i,h(r)}\leq T_r\). Missing transport links are unavailable. Missing or ambiguous logistics parameters must be finalized before implementation.

## Transportation LP

Decision variable:

\[
x_{ijg} \geq 0
\]

\(x_{ijg}\) is the quantity of blood group \(g\) transported from bank \(i\) to hospital \(j\).

Objective:

\[
\min \sum_{i,j,g} c_{ij}x_{ijg}
\]

Supply constraints:

\[
\sum_j x_{ijg}\leq S_{ig}\qquad \forall i,g
\]

Demand or shortage constraints:

\[
\sum_i x_{ijg}+u_{jg}=D_{jg}\qquad \forall j,g
\]

where \(D_{jg}\) is hospital \(j\)'s aggregate demand for group \(g\), and shortage variables \(u_{jg}\geq0\) allow the model to remain feasible. Alternatively, demand can be satisfied only up to supply by using \(\sum_i x_{ijg}\leq D_{jg}\).

Transport eligibility and deadlines can be enforced by requiring \(x_{ijg}=0\) for every bank-hospital pair that lacks an available link or is not timely for the applicable request. In this LP, units are fractional by default. The integrated model uses integer units because the dataset counts discrete packed RBC units.

## Assignment model

Binary decision variable:

\[
y_{ir}\in\{0,1\},
\]

which equals 1 if bank \(i\) is assigned to request \(r\). For the initial model, each request is assigned to at most one bank:

\[
\sum_i y_{ir}\leq1\qquad \forall r
\]

Eligibility:

\[
y_{ir}\leq e_{ir}\qquad \forall i,r
\]

Inventory limits account for exact blood-group matching:

\[
\sum_{r:g(r)=g} d_r y_{ir}\leq S_{ig}\qquad \forall i,g
\]

This form assigns the full requested quantity to an eligible bank when \(y_{ir}=1\). Unmet demand is allowed only through a separate shortage variable. To avoid hidden partial fulfillment:

\[
a_r = d_r-\sum_i d_r y_{ir}-u_r=0
\]

is not necessary. A cleaner initial interpretation is that \(y_{ir}\) represents assignment for reporting while integer request-level shipment \(q_{ir}\) determines actual partial fulfillment.

## Integrated MILP

Decision variables:

\[
q_{ir}\in\mathbb Z_{\geq0}
\]

\[
y_{ir}\in\{0,1\}
\]

\[
u_r\in\mathbb Z_{\geq0}
\]

\(q_{ir}\) is the integer number of units supplied by bank \(i\) to request \(r\), \(y_{ir}\) indicates assignment, and \(u_r\) is unmet units.

Request balance:

\[
\sum_i q_{ir}+u_r=d_r\qquad \forall r
\]

Assignment limit:

\[
\sum_i y_{ir}\leq1\qquad \forall r
\]

Shipment-to-assignment link:

\[
q_{ir}\leq d_r y_{ir}\qquad \forall i,r
\]

Eligibility:

\[
q_{ir}=0,\ y_{ir}=0\qquad \forall(i,r):e_{ir}=0
\]

If an assigned request must receive at least one unit:

\[
q_{ir}\geq y_{ir}\qquad \forall i,r
\]

Bank inventory:

\[
\sum_{r:g(r)=g}q_{ir}\leq S_{ig}\qquad \forall i,g
\]

At most one bank can supply a request, and partial delivery is represented explicitly through \(q_{ir}\) and \(u_r\). Because this initial formulation assigns at most one bank, the shipment quantity may be less than the request quantity.

## Reporting aggregates

Bank-to-hospital totals for reporting are:

\[
x_{jg}^{report}=\sum_{r:h(r)=j,\ g(r)=g}q_{ir}
\]

These totals must not be added again to objective or constraint terms.

## Emergency prioritization

The lexicographic objective has three levels:

1. \[
\min Z_1=\sum_{r\in R_E}u_r
\]
2. \[
\min Z_2=\sum_{r\in R_N}u_r
\]
3. \[
\min Z_3=\sum_{i,r}c_{i,h(r)}q_{ir}
\]

Gurobi supports hierarchical multi-objective optimization by assigning priorities to objectives; the model should solve priority 1 first, constrain or fix that optimum before priority 2, then repeat for priority 3. This global emergency objective does not use arbitrary penalty weights.

## Mathematical consistency review

- All quantities and decision variables are linear.
- Shortage variables ensure feasibility.
- At most one assigning bank is allowed per request.
- Each shipment is linked to assignment and eligibility.
- Inventory is conserved independently for each exact blood group.
- Emergency unmet units are lexicographically prioritized before normal unmet units and cost.
- Transportation cost has the correct per-unit INR scale.
- Reported bank-hospital totals are aggregates and are not included a second time in a separate objective.

## Decisions requiring finalization

- Whether partial fulfillment should remain allowed for assigned requests.
- Whether assigned banks must supply at least one unit.
- Whether a request with no deadline means unlimited delivery or still requires a clinically/operationally validated threshold.
- Whether fixed dispatch costs or blood-bank-to-hospital fixed charges should be introduced in later phases.

## Phase 4 implementation notes

The transportation LP aggregates requests by hospital, blood group, and priority. Its Emergency and Normal deadline categories are 180 and 600 minutes, matching the present dataset modeling convention. It cannot preserve two different deadlines within the same hospital/group/priority category, so this is the documented transportation-relaxation limitation.

The assignment and integrated MILPs use request-level quantities and preserve each request deadline independently. Both permit partial fulfillment by integer units and require an active assignment to receive at least one unit.
