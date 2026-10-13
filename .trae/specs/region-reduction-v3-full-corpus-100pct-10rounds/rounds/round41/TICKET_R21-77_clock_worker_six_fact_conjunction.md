# TICKET R21-77 — `clock_worker`: implement the measured six-fact conjunction (r104a)

Platform (install + re-hash first, never substitute a banked half): analyzer `1471c92eca157e46`,
generator `566ff5c502276e48`. Base on this platform: `realtime_event_source 12/13`, sole failure
`clock_worker`, `allwin delta=-113 / 7 hunks`, `win_r91 orig=1442 prod=1330 delta=-112 / 15 windows`, panel green
including `broker 128/128`.

Target is **proven reachable**: `$SP/rounds/round41/GOLD_realtime_event_source_PROOF.py` judges
`status=success units=13/13` and its `clock_worker` code object is byte-identical to the original
(`co_code` equal, `consts` equal). Ladder (see `MEASURE_R21-76_six_fact_distance_ladder.md`): restore `@6690`
holiday block → drop the spurious duplicated tail → fix the `@7164` or-chain + restore the swallowed
`system_log.debug` → fix the `@6322`/`@6496` `is_holiday` or-chains → remove the spurious `while True:` wrapper
→ **fold the `@8904` chained-compare inner `if` into its parent `elif` with `and`** (fixes jump targets
`@8972`/`@8978`).

## The bar, stated so no one re-pays for it
- Steps 1-5 can leave the unit at **`delta=0, hunks=0` and still judged** *Different control flow*: `allwin` and
  `win_r91` blank jump operands. Only the judge (`compare_pyc`, which decides CFG equivalence before bytecode) is
  authoritative. A shrinking `|delta|` is not progress; **only `units=13/13` counts**.
- Consequently a single-criterion candidate is a zero-flip candidate and gets reverted byte-exactly per the
  standing rule. Deliver the conjunction, with the halves/pair matrix showing which steps are co-requisites.
- Criteria from block/region data only: no names, no absolute offsets as keys, no counters/thresholds;
  correct-at-identification; unique membership; prefer generalizing an existing landed criterion (
  `_check_elif_chain`, `_build_basic_if_region`, `_inline_and_chain_exits_agree`, `interrupts_boolop_forward_chain`,
  `_detect_while_*_chain`, `[R21-74]`'s `_r102_run_before_child`) over a rival predicate.
- Closed: predicate-C refusal alone (`+2 → −269` collapse), R21-60 arm ordering, broad P2/D/E, the `@7248`
  manufactured-jump framing (wrong base).
- Census must join the repo ROOT when reading `corpus402.txt` (relative paths + `cwd=mirror` read all-MISS and
  print a false `CHANGED=0`); assert `files_compared=402 MISSING/FAIL=0` before believing any zero.
- Acceptance: `pyc_verify single --source <fresh product>` → `13/13`; then my own 402 sweep expecting
  `CHANGED={realtime_event_source}`; then `gate_chain 41 40` vs `rounds/round40/after`.
