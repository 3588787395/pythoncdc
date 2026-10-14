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


## Addendum 2 (orchestrator, 07:58) — r104a's in-flight candidate carries measured collateral on two other files

Reading its own sweep logs (`D:/Temp/r104/logs/sweep_f5_*.log`, analyzer at `da5d6b3717657f86`, bytes still moving,
so this is a progress reading):

| shard | `files_compared` | `MISSING/FAIL` | `CHANGED_COUNT` | changed files |
|---|---|---|---|---|
| 0+101 | 101 | 0 | 0 | — |
| 102+101 | 101 | 0 | 0 | — |
| 202+101 | 101 | 0 | **2** | `realtime_event_source.pyc`, `plugin_system_risk_calculation/__init__.pyc` |
| 303+99 | 99 | 0 | **1** | `fly/data/quote.pyc` |

Good news: its list handling is correct (`compared=101 miss=0`, no false zeros). The blocking fact is that the
current conjunction changes **three** files, where the standing bar is `changed={realtime_event_source}` — so two
conjuncts need narrowing (a risk-calculation `__init__` and `quote.pyc` are both currently-Equal files, i.e. any
change there is a regression risk the gate would score). This is the panel-canaries lesson recurring: only the
whole-corpus sweep sees it, and it saw it before a gate was spent
([[feedback-panel-canaries-not-residual-shape]]).

Hand-off state: no candidate is installable yet; the target (`13/13`, oracle byte-identical) and the scoring rig
are both proven, and the remaining work is narrowing these three conjuncts to the victim file alone.


## Addendum 3 (orchestrator, 08:20) — the conjunction's collateral is now clean; the flip is not

Pinned reading of r104a's `f5b` (analyzer `996a1b1acf143458`, generator untouched at `566ff5c502276e48`; bytes were
still moving, so this is a progress state and the candidate is banked as `CANDIDATE_r2177_f5b_996a1b1acf143458.py`):

* its own sharded 402 sweep: `compared 101/101/101/99, miss=0`, `CHANGED_COUNT 0/0/1/0`, and the one changed file is
  **`realtime_event_source.pyc`** — the `plugin_system_risk_calculation/__init__.pyc` and `fly/data/quote.pyc`
  collateral from addendum 2 is gone, so the conjuncts are now victim-scoped.
* my rig on its newest product (`out/pnl_realtime.py`): `hunks_vs_ORACLE=4`, `instrs=-114 jsites=-9`,
  `indeg-equal=False`, judge `12/13` *Different control flow*.

So this state is **installable in shape but not in substance**: zero collateral without yet reaching `13/13`, which is
exactly the zero-flip condition the standing rule reverts. Remaining gap against the oracle is ladder steps 3–6
(the `@7164` and `@6322`/`@6496` or-chains, the spurious `while True:` wrapper, and the `@8904` chained-compare
fold that fixes the two jump targets `@8972`/`@8978`).


## Addendum 4 (orchestrator, 08:30) — r104a delivered [R21-77-F5]: clean, real, and still zero-flip

Delivered analyzer `996a1b1acf143458` (generator untouched at `566ff5c502276e48`, repo `core/` re-hashed by the
engineer as unchanged), banked here as `CANDIDATE_r2177f5_996a1b1acf143458.py`.

* **What it fixes is principled**: it replaces the landed wrapper-removal's `len(body_outer − body_inner) <= 2`
  **counter** — itself a rule violation — with three structural clauses (the inner test-block exit cannot re-reach
  the shared test block; every wrapper-exclusive body block is the shared test, or inside the real loop's own span
  and is therefore **reclaimed** per principle 2, or is unreachable post-exit code; the wrapper's back-edge block
  lies inside the real loop's body). Root cause it names: `WHILE` regions `@5598` and `@5614` are both driven by the
  **same test block `@5598`** (`condition_block == header`), a principle-2 violation, and the wrapper over-absorbs
  `@6690 @6702 @6778` plus `@9210 @9214`, which is *why* the holiday branch was `break`-stubbed and duplicated.
* **Measured effect**: ladder step 5 collapses, plus step 1's holiday half and 4 of step 2's 5 lines —
  `allwin −113/6`, `win_r91 −114/9 windows`, oracle text distance `+84/−74 → +66/−53`. Judge **still 12/13**.
* **Collateral discipline worked**: its first variant `da5d6b3717657f86` broke two currently-Equal units
  (`quote 92/92→91/92`, `risk __init__ 43/43→42/43`) and was falsified and not delivered; the delivered variant's
  corpus sweep reads `files_compared=402 MISSING/FAIL=0 CHANGED=1={realtime_event_source}`, panel 20/20,
  **broker 128/128 unmoved**, battery `RED=8/9`. Four of its six census fires are inert (zero product bytes).

**Therefore F5 is a banked co-requisite, not a landing** (zero-flip rule), and the remaining distance is now
explicitly four blocked facts: step 3 (`@7164` or-chain with the `system_log.debug` sitting in another region's
merge — the same −6 falsified four ways), step 4 (`@6322`/`@6496`, same rule), step 6 (`@8904` chained-compare fold,
blocked because `IF_THEN_ELSE @8948` declares the back edge `@9194` as its merge so the chain-continuation reading is
not available from region data), and the 112-instruction `@7972..@8586` half of step 1 (reachable today only through
the over-absorbing `elif_final_else`, so it needs a **positive tail claim**, not a narrower refusal).

Next dispatch must build on F5 (`996a1b1acf143458`), not on the landed analyzer, and must treat step 6's merge
declaration as an analyzer-side region-data problem with a named obstacle rather than as a text fix.
