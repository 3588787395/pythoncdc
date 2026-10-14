# R21-37 banked half re-measured on the gate-37 base

Engineer r64a flagged this as debt: its candidate was built against generator `37997bdac555b2e9`
+ analyzer `efd455859b69d8a1`, and gate 37 moved both files. Re-measured in my own mirror by
installing `CANDIDATE_r64a_R21-37_ternary_join_BANKED_not_landed.py` (analyzer
`9f229b71bb95ddb4`, anchor unique at `:25056`) over the landed pair
(`20fa73b4e8231f0f` + `c069d359cbfe76b0`).

Result, identical to the pre-gate-37 reading: `trade_live_broker :: _process_order`
`len orig=507 prod=465 delta=-42` (from `-68`), broker file held at **125/128**, the only panel
change being the broker product's bytes, and the first remaining window is
`delete orig[340..348 @2092..@2152] del=8` — i.e. one of the four interior `.format(...)` host
statements r64a showed are never dispatched.

So the half is still valid and still not landable: no unit flip. What gates `_process_order` now is
the generator-side region-scheduling gap (interior `TernaryRegion` members of a chain never reach
`_generate_ternary`: of sites 1634/2092/2236/2310/2430/2574 only 1634 and 2430 are dispatched), and
r64a measured that forcing the classification wider makes that worse, not better (`-97/4` relaxed,
`-104/26` consumer-restricted). Recorded on the ticket as the next mechanism; mirror restored to the
landed bytes and `cmp`-proved, repo clean.

