# Home KPI Overlap Fix Tracker

| ID | Subtask | Status | Outcome |
|---|---|---|---|
| K1 | Inspect Home KPI layout and theme CSS | DONE | Root cause identified: negative `margin-bottom` on the highlighted label pulled the nested metric value upward. |
| K2 | Fix shared KPI spacing and alignment | DONE | Replaced the negative margin with positive spacing in the shared application CSS; red accent retained. |
| K3 | Compile and run dashboard regression tests | DONE | `compileall` passed; `tests/test_dashboard.py` passed with 3 tests. |
| K4 | Verify all seven KPI cards and document visual QA limits | DONE | Dashboard smoke test returned HTTP 200 on port 8502; all KPI cards use the shared renderer. Browser visual inspection remains unavailable. |
