# MEASURE_R21-89 — fold-window guard completion (engineer r115a, round 41)

Mirror `D:/Temp/r115` (layout copied from `D:/Temp/r113`; `r91m` and `r106`–`r113` untouched).
Reference repo read-only throughout: no repo `core/` or `site-packages/` edit, no git write command,
no `*OK.py` hand-edit. Every product came from `pycdc.py` with the previous product deleted and its
size checked (crash stubs read 0 / ~99 B; every product here is 20–21 kB). Platform pinned all
session: analyzer `996a1b1acf143458` = `[R21-77-F5]`, generator `47d44ec51fa325c5` = `[R21-88]`;
every arm/panel/collar/sweep command ends with
`[restore] ana=996a1b1acf143458(True) gen=47d44ec51fa325c5(True)` in the SAME command.
`[R21-86] 59a405837c22a4cb` (parity-by-cancellation) was not used as base, and the `[R21-79]`
analyzer half `3ad5ceaa23135334` was not paired.

Rigs: `rounds/round41/oracle_diff_r104.py` (prints `ours`, `DELTAS instrs/back/jsites`,
`indeg-equal`, judge line) and `rounds/round41/hunk_attribution_r107.py`; both live under
`REPO/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round41/`.

## 0. Base reproduced before any edit

`rig/arm_r115.py BASE F5 base0 --files 1` → product `out/rt_base0.py` 20906 B / 20544 B CR-stripped,
`ours=256 ORACLE=254`, `hunks_vs_ORACLE=8`, `instrs=-25 back=+0 jsites=-4`, `indeg-equal=False`,
judge `12/13 Different control flow`. Byte-for-byte the brief's base row.

## 1. Matrix — `clock_worker` against the byte-identical 13/13 oracle (254-line body)

| # | arm | analyzer | generator sha16 | ours | instrs | back | jsites | hunks_vs_ORACLE | indeg-equal | judge |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | control: the oracle itself (rig-certified rows 0 of r104/r107) | — | — | 254 | +0 | +0 | +0 | 0 | True | `13/13` |
| 1 | base `[R21-88]`, reproduced by me | F5 | `47d44ec51fa325c5` | 256 | -25 | +0 | -4 | 8 (2 of them structural, 12-line and 8-line) | False | `12/13 Different control flow` |
| 2 | **residual A only** — arm face, `abl_r2189_armonly.py` | F5 | `4b988da14af58d41` | 256 | **-20** | **+0** | **-3** | 9 | False | `12/13` |
| 3 | **residual B only** — inherited-continuation face, `abl_r2189_elseonly.py` | F5 | `fd28f04040cdb2cd` | 256 | **-18** | **+0** | -4 | 7 | False | `12/13` |
| 4 | **shipped `[R21-89]`, both faces** | F5 | **`cb8c2c7928672abd`** | **256** | **-13** | **+0** | **-3** | **8** (4 parenthesisation + `return` + residual C + 2 tail; the two structural hunks of row 1 are gone) | False | `12/13 Different control flow` |
| 4b | rejected: pass placed in the pre-dispatch pre-pass, every branch list scanned | F5 | `301e491d4da74670` | 244 | -96 | +0 | -7 | 8 | False | `12/13` — declared guards at `@426 @2838 @8964` outside any fold; overshoot below 254 ⇒ rejected |
| 4c | rejected: same placement, exception escaping the pass | F5 | `3eced242a4cc35f0` | 195 | **-485** | **-4** | -59 | 2 | False | `11/13` — reproduces the excluded `-485` collapse; pre-pass bodies must be failure-isolated |
| 4d | rejected: row 4 + arm-tail claim sorted by block offset | F5 | `0412b9077d1e3f42` | 256 | -13 | +0 | -3 | 8 | False | `12/13` — product **byte-identical to row 4** (20608 B CR-stripped), i.e. metrics-inert ⇒ reverted, row 4 shipped |

Both hunk readings are given because the rigs segment differently (`oracle_diff_r104.py` uses
`n=0`, `hunk_attribution_r107.py` uses `n=2`): row 1 = 8/5, row 2 = 9/6, row 3 = 7/4,
row 4 = 8/5. The count is not the signal here — row 4's hunks are *size-shrunk*: the 12-line
structural hunk at `@@ -194,12` (residual A) became a 1-line parenthesisation difference and the
`@@ -238,3` ladder hunk disappeared entirely, which is what the `instrs`/`jsites` movement reports.

Bar 1 **met on both instruction metrics**: `instrs -25 → -13` and `jsites -4 → -3` move toward 0
together with `back=+0` kept, and `ours` stays 256 (no overshoot below 254 — the +2 is the tail
`else:`/`return None` pair of open axis 2). Rows 2 and 3 show the two faces are independently
productive and row 4 pays each once, not twice (`-20` and `-18` alone, `-13` together).
`indeg-equal` did **not** flip — with residual C and the flat chained-compare leg still open the CFG
has not converged.

## 2. Ten-file collateral smoke (CR-stripped product vs committed `*OK.py`)

Row 4, `rig/arm_r115.py out/cand_r2189.py F5 smoke6 --files 6` then
`rig/collar_r115.py out/cand_r2189.py tail4 …` (five-file first call, four-file second):

| file | result |
|---|---|
| realtime_event_source.pyc | **CHANGED ours=20608 committed=20205** (intended) |
| trade_live_broker.pyc (largest collateral) | IDENTICAL |
| klinedata.pyc | IDENTICAL |
| fly/data/quote.pyc | IDENTICAL |
| real_quote.pyc | IDENTICAL |
| fly/data/quotation.pyc | IDENTICAL |
| order_api.pyc | IDENTICAL |
| replace_utils.pyc | IDENTICAL |
| risk-calculation `function.pyc` | IDENTICAL |
| handlers.pyc | IDENTICAL |

Bar 2 **passed**: `CHANGED=[]` over the nine collateral files; the rule fires only in the victim.

## 3. Twenty-file panel, `rounds/round38/PANEL_20files.txt`, paired BY INDEX

Row 4 + pinned F5, five shards `rig/panel_r115.py v4p out/cand_r2189.py F5 <start> <count>`
(0-2, 3-6, 7-10, 11-14, 15-19); log `logs/panel_v4p.txt`. Index pairing, never basename — rows 14-16
are the three `arg_checker` copies and 17-19 the three `profiler_func` copies.
"before" = `[R21-88]` row 5 of `MEASURE_R21-88.md`.

| idx | panel row | before | after (row 4) | bytes |
|---|---|---|---|---|
| 00 | fly/data/quotation | 153/153 | 153/153 | SAME |
| 01 | fly/data/quote | 92/92 | 92/92 | SAME |
| 02 | klinedata | 64/64 | 64/64 | SAME |
| 03 | handlers | 30/30 | 30/30 | SAME |
| 04 | wizard_quant_api | 58/58 | 58/58 | SAME |
| 05 | trade_info_utils | 41/41 | 41/41 | SAME |
| 06 | api_base | 28/28 | 28/28 | SAME |
| 07 | real_quote | 45/45 | 45/45 | SAME |
| 08 | strategy | 27/27 | 27/27 | SAME |
| 09 | order_api | 37/37 | 37/37 | SAME |
| 10 | **trade_live_broker** | 128/128 | **128/128** | SAME |
| 11 | matcher | 17/17 | 17/17 | SAME |
| 12 | realtime_event_source | 12/13 fail | 12/13 fail (Different control flow) | DIFF 20608/20205 (intended) |
| 13 | risk `__init__` | 43/43 | 43/43 | SAME |
| 14 | IQCommon/arg_checker | 49/49 | 49/49 | SAME |
| 15 | IQData/utils/arg_checker | 39/39 | 39/39 | SAME |
| 16 | IQEngine/utils/arg_checker | 43/43 | 43/43 | SAME |
| 17 | IQCommon/profiler_func | 17/17 | 17/17 | SAME |
| 18 | IQData/utils/profiler_func | 15/15 | 15/15 | SAME |
| 19 | IQEngine/utils/profiler_func | 18/18 | 18/18 | SAME |

Bar 3 **passed**: every currently-`Equal` row unchanged with the same unit count and `failing=0`,
`broker 128/128` included; zero regression.

## 4. ROOT-joined 402-file sweep

`rig/sweep_r115.py v4s out/cand_r2189.py F5 <start> <count>`; roster
`rounds/round40/r95/corpus402.txt` is repo-relative and is joined with
`ROOT = D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` (printed by every shard header), the
script asserts `len(paths) == 402` before comparing and prints `files_compared` / `MISSING/FAIL`
per shard, so a `CHANGED_COUNT 0` is only readable with `files_compared == shard size` and
`MISSING/FAIL 0` (pattern `D:/Temp/r91m/sweep_r102.py`).

| shard | files_compared | MISSING/FAIL | CHANGED_COUNT |
|---|---|---|---|
| [0,100) | 100 | 0 | 0 |
| [100,200) | 100 | 0 | 0 |
| [200,300) | 100 | 0 | **1** = `site-packages\IQEngine\plugins\plugin_system_event_source\realtime_event_source.pyc` ours=20608 committed=20205 |
| [300,402) | 102 | 0 | 0 |
| **total** | **402** | **0** | **CHANGED = {realtime_event_source.pyc} only** |

Bar 4 **passed**. (`STUBS 13/10/7/12` are the rig's separate `SMALL len=` notices, not comparison
failures: each of those products still matched its committed `*OK.py` byte-for-byte.)

## 5. Judge, residual state, install recommendation

Judge: **`12/13`, `Different control flow` — `13/13` was NOT reached.** The corpus stays
6616/6617 units, 401/402 files; the only failing unit is still
`<module>.RealtimeEventSource.clock_worker`.

What row 4 closed (verified in the product against the oracle):
`if now_date != self.first_run_date:` is emitted with its two siblings inside it and the arm
continuation sequential (`@@ -194,12` hunk reduced to a parenthesisation-only 1-line difference),
and `elif check_trading_time(am_open, am_close, pm_open, pm_close, pm_over, …):` is emitted as a
ladder leg at gold's indentation with its `if check_handle_date(...)/else:` body.

What is still open (2 structural hunks):
1. `@@ -185,3 +185,3 @@` **residual C** — structural, but NOT the walk-coverage cause of A:
   measured at `@6496` the fold's arm window is `[6580, 6582, 6652]` and holds no bare condition
   block; `@6690` (`if holiday_not_do_before == '0'`) **is** a region entry
   (`IfRegion@6690`, `cond=6690`, `merge=6778`, parent `IfRegion@6548`, itself a leg of this fold),
   while `@6690/@6702/@6778` sit in the *parent* `IfRegion@6280.then_blocks`. The dedent is an
   arm-window **under-declaration** — the positive direction of the tail-ownership axis, where the
   already-excluded `[R21-79]` positive-tail-claim and ledger-claim shapes live. Not attempted.
2. `@@ -246,4 +245,0 @@` / `@@ -251,0 +248,6 @@` — the second ladder leg still renders nested
   (`if A and B:` + `if delay_after_trading >= now_time >= after_trading:` instead of one flat
   `elif A and B and x <= t <= y:`), and the loop tail still materialises
   `else:` / `return None` (this is also the whole of the remaining `+2` in `ours=256`).

**Install recommendation: NOT installable** — `installable` is reserved for judge `13/13` with
`CHANGED={realtime_event_source}` and zero panel regression; here bars 1–4 are met and the judge did
not flip, so **bank `cb8c2c7928672abd` as `[R21-89]`**. It is the first arm to emit both swallowed
tests with `back=+0`, halving the instruction distance (`-25 → -13`) at zero collateral and zero
panel regression, and it closes the `elif check_trading_time` leg identity at the correct level.
Next axis, in the order the remaining diff reads: the flat chained-compare leg plus the loop-tail
`else: return None`, then the `@6496` arm-window under-declaration.

## 6. Artifacts

`D:/Temp/r115/DELIVER/{PATCH_R21-89_region_ast_generator.py,
CANDIDATE_r2189_cb8c2c7928672abd.py, FIX_R21-89_two_residual_ladder_legs.md, MEASURE_R21-89.md}`;
ablations `D:/Temp/r115/abl_r2189_armonly.py` (`4b988da14af58d41`),
`abl_r2189_elseonly.py` (`fd28f04040cdb2cd`); rejected sub-shapes are rows 4b–4d (not installed,
`out/cand_r2189.py` overwritten by the shipped bytes); products
`out/rt_base0.py`, `out/rt_v2.py`, `out/rt_v4.py`, `out/rt_v6.py`, `out/panel_v4p_*.py`; rig logs
`logs/oracle_*.txt`, `logs/attr_*.txt`, `logs/panel_v4p.txt`, `logs/trace_*.txt`,
`logs/census_a.txt`, `logs/decl.txt`, `logs/decl2.txt`, `logs/diag_guard.txt`. Instrumentation was
runtime monkeypatching only, each probe run re-hashing `core/cfg` and diffing its product against
the un-probed base product (`[inertness] … identical=True`); no in-source probe was ever written.
Every command finished inside the 300 s budget.

## 7. Untrusted text

Tool outputs this session again carried instruction-looking content that is not the ticket (the
skill-listing reminder block and comments in committed source addressed to other engineers). Treated
as data only, mentioned once, scope kept.
