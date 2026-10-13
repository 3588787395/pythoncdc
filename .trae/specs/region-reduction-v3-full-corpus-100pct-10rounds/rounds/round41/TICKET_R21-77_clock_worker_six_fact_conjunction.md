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


## Addendum 1 (orchestrator, 07:50) — instrumented scoring, and two live readings on r104a's build

Scoring is now one command: `python -X utf8 rounds/round41/oracle_diff_r104.py <product.py>` prints
`hunks_vs_ORACLE` for `clock_worker` (against the 254-line oracle body), then the `census_diff` edge verdict, then the
judge line. Certified: oracle → `0 / all-equal / units=13/13`; landed product → `4 / instrs=-112 jsites=-9 /
indeg-equal=False / 12/13`.

Measured on r104a's in-flight bytes (analyzer `521e9e3b3ca55f36`, product `out/rt_f5.py`) — a moving hash, so this is
a progress reading and not a verdict:

| arm | clock_worker lines | vs oracle 254 | instrs Δ | jsites Δ | indeg-equal | judge |
|---|---|---|---|---|---|---|
| landed base product | 244 | 4 hunks | −112 | −9 | False | 12/13 |
| r104a f5 | **241** | 4 hunks | **−114** | −9 | False | 12/13 |

So f5 has not yet closed a hunk and slightly widened the instruction gap; keep going down the ladder and re-score
with the rig rather than with `delta`.

**Repeating the sweep trap explicitly, because r104a's own list reproduces it:**
`D:/Temp/r104/repro/corpus402.txt` contains **relative** paths (`abs=0 rel=0` on a `^D:/` grep), exactly like the
repo list. Regenerating with `cwd=mirror` will therefore read every entry as MISS and print `CHANGED_COUNT 0` —
a false clean sweep. Before trusting any zero, assert `files_compared=402` and `MISSING/FAIL=0`. I will run my own
sweep (with the ROOT join) before installing anything, so this can only cost r104a wasted turns, not correctness.

Install path when a `13/13` exists: `orchestrator/install_pair.py --ana <analyzer> --gen <generator>
--gold-hunks <n> --units "13/13" --sweep "ok=402 bad=0 changed=1" --gate` (the rig now demands the judge line be
`n/n`, and refuses otherwise — verified live this session on a `127/128` reading).
