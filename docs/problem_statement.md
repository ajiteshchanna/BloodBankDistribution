# Problem Statement

## Real-world problem

The project addresses allocation of available packed red blood cell (RBC) units from blood banks to hospitals after hospital requests are known. It is a planning exercise for choosing which units to transport and how emergency shortages should be prioritized.

## Planning scope

The synthetic case contains 5 blood banks, 8 hospitals, 8 ABO/Rh blood groups, and 32 hospital requests. The planning horizon is represented by each request's maximum delivery time. It is not a live emergency-dispatch system.

## Supply and demand

Each bank has a fixed inventory in units for each blood group. Each hospital request specifies one blood group, a positive quantity, a priority, and a maximum delivery time. For this academic model, only exact ABO/Rh matching is allowed.

## Transportation

Each bank-hospital corridor has an estimated distance, delivery time, and cost per unit. Corridors may be unavailable through the `available` field. Missing corridors are treated as unavailable.

## Decisions

The later models may decide:

- shipment quantities from banks to hospital requests;
- whether a bank is assigned to a request;
- the number of unmet units for each request.

## Assumptions and limitations

- The source data is entirely synthetic teaching data, not real hospital or blood-bank records.
- The packed RBC units are treated as divisible in the transportation LP and integer quantities are used in the assignment and integrated models.
- Exact ABO/Rh blood-group matching is a simplified allocation rule, not a clinical transfusion compatibility model.
- Transportation cost is measured per unit in INR.
- An eligible bank must hold the request blood group, have an available corridor, and meet the request delivery deadline.
- Shortages are valid scenarios and do not make validation fail.
