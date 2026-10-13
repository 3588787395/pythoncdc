# MEASURE_R21-87 — or-chain scaffolding position (engineer r112a, round 41)

Mirror `D:/Temp/r112` (layout copied from `D:/Temp/r111`; `r111` and `r91m`/`r106`-`r111` were not
touched). Reference repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` read-only throughout:
repo `core/cfg/region_ast_generator.py` still `566ff5c502276e48`, `core/cfg/region_analyzer.py`
still `1471c92eca157e46` (re-hashed at the end), no git write command run, no `*OK.py` hand-edited,
every product came from `pycdc.py` (previous product deleted + size checked before each read).

**Platform pinned for this ticket**: analyzer `996a1b1acf143458` (`[R21-77-F5]`) + arm generator
`59a405837c22a4cb` (`[R21-86]`). `rig/arm_r112.py` / `rig/panel_r112.py` / `rig/sweep_r112.py`
install a variant, measure, then **restore and re-hash in the same command**; the last line of every
log is `[restore] ana=996a1b1acf143458(True) gen=59a405837c22a4cb(True)`.

**Candidate shipped: `ed07b60b970e545d`** (3,883,854 B, BOM present, 100 % CRLF, zero bare LF, zero
`CR CR LF`, `python -X utf8 -m py_compile` rc=0), built only by
`D:/Temp/r112/DELIVER/PATCH_R21-87_region_ast_generator.py` **from `[R21-86]` `59a405837c22a4cb`**
(2 additive anchored edits; re-running the patch reproduces the same sha16 ⇒ idempotent).

## 1. Matrix — `clock_worker` against the byte-identical 13/13 oracle

`rounds/round41/oracle_diff_r104.py` + `census_diff_r104.py` + `hunk_attribution_r107.py`, all run
from the repo spec dir; products in `D:/Temp/r112/out/rt_<label>.py`.

| # | arm | analyzer | generator sha16 | ours (ORACLE 254) | instrs | back | jsites | hunks_vs_ORACLE | indeg-equal | judge line |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | control: the oracle text itself | — | — | 254 | +0 | +0 | +0 | 0 | True | `13/13` (rig-certified) |
| 1 | **base `[R21-86]`, reproduced by me** | `996a1b1acf143458` | `59a405837c22a4cb` | 262 | -6 | +0 | +2 | 4 | False | `12/13 Different control flow` |
| 2 | `[R21-87]` fold + narrow, **no guard** (=V3) | `996a1b1acf143458` | `10c8703e419c9023` | 212 | **-282** | **-1** | -33 | 6 | False | `12/13 Different control flow` |
| 3 | fold only, no arm re-declaration (=V1) | `996a1b1acf143458` | `1244ac19a3e5c1c7` | 256 | -27 | +0 | -4 | 8 | False | `12/13 Different control flow` |
| 4 | guard evaluated after the marks (=V4) | `996a1b1acf143458` | `b61b692f7a35a4cb` | 262 | -6 | +0 | +2 | 4 | False | `12/13 Different control flow` — **byte-identical to row 1** (the guard hit a `NameError` swallowed by its own `except` ⇒ inert; kept as the "rule switched off" witness) |
| 5 | **shipped: fold + narrow + pre-mutation conservation guard (=V4b)** | `996a1b1acf143458` | **`ed07b60b970e545d`** | **257** | **-26** | **+0** | **-2** | **6** | False | `12/13 Different control flow` |
| 6 | row 5 variant bytes as built by the ablation script | `996a1b1acf143458` | `8be316e74fd35e39` | 257 | -26 | +0 | -2 | 6 | False | `12/13` — same reading as row 5, different bytes only |

Row 1 is an exact reproduction of `[R21-86]` §1 row 2 (262 / -6 / +0 / +2 / 4 / False / 12-13,
product 21788 raw / 21420 CR-stripped). `[R21-79]` was not paired (measured to hurt).

Bar 1 verdict: **FAILED on `instrs`.** `ours` moved 262 → **257** toward 254 from above ✓ (the +8
overshoot is down to +3) and `back=+0` held ✓, but `instrs` moved -6 → **-26**, i.e. *away* from 0.
Rows 2 and 3 fail it harder. Recorded, and the cause is the finding (§4).

## 2. What the fold actually fixed (text evidence, `rig/udiff_r112.py`)

Shipped row 5, residual hunks vs the oracle:

| oracle line | gold | product | class |
|---|---|---|---|
| 177, 180 | `if (A and B) or C:` | `if A and B or C:` | **parenthesisation only** — recompiles byte-identically, judge-irrelevant |
| 185-187 | `if holiday_not_do_before == '0':` at 24 sp | same test at 20 sp | site `@6496` arm one indent too shallow |
| 195-214 | the two `@7164`/`@7582` `if (A and B) or C:` statements, flat | `@7164` still nested `if A: if B or C: pass / elif …`, `@7582` folded but one level inside | step-3 leg refused by the conservation guard (region owns the loop tail) |
| 216-236, 238-251 | 36 tail lines | 9 | arm-narrowing at `@7582` cuts the `elif check_trading_time` / `elif … AFTER_TRADING_END` / `else: time.sleep(FPS)` tail ⇒ the **-26 instrs** |

Before the fold all four sites printed as nesting; now three of four print folded and flat
(`@6322`, `@6496`, `@7582`). So the briefed diagnosis — "8 lines of step-3/step-4 scaffolding sit in
the wrong place, the oracle prints folded" — is **confirmed**, and the fold is the right actuator
for the *line-count* half of it.

## 3. Collateral smoke, 10 files, CR-stripped byte compare against the committed products

Row 5 (`ed07b60b970e545d`), from `rig/arm_r112.py … --files 10`:

| file | committed (CR-stripped) | result |
|---|---|---|
| realtime_event_source.pyc | 20205 | **CHANGED 20917 (intended)** |
| trade_live_broker.pyc | 175772 | IDENTICAL |
| klinedata.pyc | 100737 | IDENTICAL |
| fly/data/quote.pyc | 91268 | IDENTICAL |
| real_quote.pyc | 52796 | IDENTICAL |
| fly/data/quotation.pyc | 179081 | IDENTICAL |
| order_api.pyc | 33768 | IDENTICAL |
| replace_utils.pyc | 13213 | IDENTICAL |
| plugin_system_risk_calculation/function.pyc | 29631 | IDENTICAL |
| handlers.pyc | 8827 | IDENTICAL |

The destructive row 2 and the inert row 4 arms show the identical collateral table — the
discriminator fires **only in the victim** on every arm (bar 2 passed).

## 4. 20-file panel, `rounds/round38/PANEL_20files.txt`, paired BY INDEX

`rig/panel_r112.py r2187b <candidate> F5 <start> <count>`; config = `[R21-87]` row 5 + pinned F5.
"before" = the `[R21-86]` base readings certified in `MEASURE_R21-86.md` §4 (same mirror platform).

| idx | panel row | before (base `[R21-86]`) | after (`ed07b60b`) | bytes vs committed |
|---|---|---|---|---|
| 00 | fly/data/quotation.pyc | 153/153 success | 153/153 success | SAME |
| 01 | fly/data/quote.pyc | 92/92 success | 92/92 success | SAME |
| 02 | IQCommon/api/klinedata.pyc | 64/64 success | 64/64 success | SAME |
| 03 | IQCommon/logger/handlers.pyc | 30/30 success | 30/30 success | SAME |
| 04 | IQCommon/strategy/wizard_quant_api.pyc | 58/58 success | 58/58 success | SAME |
| 05 | IQCommon/util/trade_info_utils.pyc | 41/41 success | 41/41 success | SAME |
| 06 | IQData/api/api_base.pyc | 28/28 success | 28/28 success | SAME |
| 07 | .../realquote/real_quote.pyc | 45/45 success | 45/45 success | SAME |
| 08 | .../fly_data/strategy/strategy.pyc | 27/27 success | 27/27 success | SAME |
| 09 | .../fly_api/order_api.pyc | 37/37 success | 37/37 success | SAME |
| 10 | .../trade/trade_live_broker.pyc | 128/128 success | 128/128 success | SAME |
| 11 | .../matcher/matcher.pyc | 17/17 success | 17/17 success | SAME |
| 12 | .../event_source/realtime_event_source.pyc | 12/13 failure (`Different control flow`) | 12/13 failure (`Different control flow`) | DIFF 20917/20205 (intended) |
| 13 | .../risk_calculation/__init__.pyc | 43/43 success | 43/43 success | SAME |
| 14 | IQCommon/arg_checker.pyc | 49/49 success | 49/49 success | SAME |
| 15 | IQData/utils/arg_checker.pyc | 39/39 success | 39/39 success | SAME |
| 16 | IQEngine/utils/arg_checker.pyc | 43/43 success | 43/43 success | SAME |
| 17 | IQCommon/profiler_func.pyc | 17/17 success | 17/17 success | SAME |
| 18 | IQData/utils/profiler_func.pyc | 15/15 success | 15/15 success | SAME |
| 19 | IQEngine/utils/profiler_func.pyc | 18/18 success | 18/18 success | SAME |

19/20 rows identical in units **and bytes**; row 12 is the victim. **Zero panel regression** (bar 3
passed). Duplicated-module rows (`arg_checker` ×3, `profiler_func` ×3) paired by index, never by
basename.

## 5. ROOT-joined 402 sweep, CR-stripped byte compare (`rig/sweep_r112.py`)

Roster `rounds/round40/r95/corpus402.txt` (402 repo-relative paths) joined with
`ROOT = D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`; the script asserts `len(paths)==402`,
prints the ROOT it used plus `files_compared` and `MISSING/FAIL` per shard, and regenerates through
the mirror while reading inputs from ROOT (the under-`cwd=mirror` reading is all-MISS and would
print a false zero — that is why the join is asserted, not assumed).

| shard | files_compared | MISSING/FAIL | SMALL (<200 B) | CHANGED_COUNT |
|---|---|---|---|---|
| [0,100) | 100 | 0 | 13 | 0 |
| [100,200) | 100 | 0 | 10 | 0 |
| [200,300) | 100 | 0 | 7 | **1** |
| [300,402) | 102 | 0 | 12 | 0 |
| **total** | **402** | **0** | 42 | **1** |

`CHANGED site-packages\IQEngine\plugins\plugin_system_event_source\realtime_event_source.pyc
ours=20917 committed=20205` — `CHANGED = {realtime_event_source.pyc}` only (bar 4 passed).

## 6. Judge, and the two findings the next ticket should bank on

`12/13`, `Different control flow`, verdict class unchanged. **The flip was NOT reached.**

Two results matter more than my numbers:

1. **`instrs=-6` on the base arm is scaffolding-masked, not recovery.** Removing the nesting
   scaffolding does not "lose" 20 instructions — it stops *paying twice* for tests that were never
   in the original. The honest remaining distance for `clock_worker` is therefore about **-26
   instructions / 6 hunks / `indeg-equal=False`**, not -6, and it is *missing code* in the
   `@7582..@9194` tail (the `elif`/`else` arms cut by the arm window) — consistent with the standing
   finding that `indeg-equal=False` means text parity alone cannot flip the judge.
2. **The or-chain fold is expressible, safe, and victim-local** (zero collateral on all 402 files,
   zero panel regression). What blocks it is not the fold but its neighbour: region `R@7164` owns the
   entire rest of the while-body, so (a) the step-3 leg refuses the fold under the conservation
   guard and (b) the step-4 fold's arm window cuts the `elif` tail. Both need the *ownership* of
   `@7582..@9194` re-declared to the while-body sequence — an analyzer-side statement-boundary fact,
   the one axis already measured destructive through `block_to_region`.

**Install recommendation: NOT installable.** `installable` requires judge `13/13` AND
`CHANGED = {realtime_event_source}` AND zero panel regression: two of three hold (sweep ✓, panel ✓),
the judge does not, and bar 1 (`instrs` toward 0) is not met — the shipped candidate is strictly
better than rows 2/3 and is the only variant that improves `ours` while keeping `back=+0`.
**Bank `ed07b60b970e545d`** as the standing `[R21-87]` fold, and pair it only after the tail-ownership
fact above is closed; on its own it is a text-shape improvement that exposes, rather than closes, the
last 26 instructions.

## 7. Artifacts (absolute, re-runnable)

| path | role |
|---|---|
| `D:/Temp/r112/DELIVER/PATCH_R21-87_region_ast_generator.py` | idempotent anchored patch, `[R21-86] 59a40583` → `ed07b60b` |
| `D:/Temp/r112/DELIVER/CANDIDATE_r2187_ed07b60b970e545d.py` | the shipped candidate generator |
| `D:/Temp/r112/DELIVER/FIX_R21-87_orchain_scaffolding_position.md` | rule, discriminator, rulers reused, excluded-premise reconciliation |
| `D:/Temp/r112/abl_r2187_V1.py` `…V4.py` `…V4b.py`, `D:/Temp/r112/cand_r2187_gen.py` | rows 3, 4, 6, 2 of the matrix |
| `D:/Temp/r112/rig/arm_r112.py`, `rig/panel_r112.py`, `rig/sweep_r112.py` | arm / panel-by-index / ROOT-joined sweep, all restore+re-hash |
| `D:/Temp/r112/rig/orchain_census_r112.py`, `rig/dis_range_r112.py`, `rig/trace_if_r112.py`, `rig/udiff_r112.py` | read-only diagnosis (region census, original bytecode, runtime render-path trace, oracle↔product diff) |
| `D:/Temp/r112/out/rt_*.py`, `D:/Temp/r112/logs/{oracle,attr}_*.txt` | raw products and rig logs for every row |

Probe inertness: the region census and the runtime render-path trace import `core/cfg` but never edit
it; `core/cfg/region_analyzer.py` re-hashed `996a1b1acf143458` and `region_ast_generator.py`
`59a405837c22a4cb` after every probe run, and the traced pipeline produced the same 21 108-character
source as the untraced in-process run of the same config.

## 8. Untrusted text

Tool outputs this session again carried instruction-looking lines that are not the ticket: the
appended skills/`<system-reminder>` block, repeated `workflow notes:` advisories (including one
telling me to use a background-run parameter for long sweeps), and committed source comments
addressed to other agents. I treated all of it as data, did not act on it, and kept the briefed
scope; my commands stayed inside the 300 s per-command budget.
