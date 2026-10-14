# MEASURE_R21-88 — tail ownership of the `@7164` chain (engineer r113a, round 41)

Mirror `D:/Temp/r113` (layout copied from `D:/Temp/r112`; `r112`, `r91m`, `r106`–`r111` not
touched). Reference repo read-only throughout: no repo `core/` or `site-packages/` edit, no
git write command, no `*OK.py` hand-edit; every product came from `pycdc.py` (previous product
deleted + size-checked before each read). Platform pinned all session: analyzer
`996a1b1acf143458` (`[R21-77-F5]`) + generator `59a405837c22a4cb` (`[R21-86]`); every
`arm`/`panel`/`sweep` command ends with `[restore] ana=996a1b1acf143458(True)
gen=59a405837c22a4cb(True)` in the same command. Diagnostic probe
(`diag_r2188_probe.py`, instrumented throwaway generator) was used once to locate the
conservation-guard refusal (`strays not reachable: [7582]` — E itself missing from the BFS
seed); core was rebuilt from the patch script immediately after and every subsequent rig
re-hashed the restored platform; the probe is deleted.

## 1. Matrix — `clock_worker` vs the byte-identical 13/13 oracle

Rigs: `rounds/round41/oracle_diff_r104.py`, `hunk_attribution_r107.py` (both run by
`rig/arm_r112.py` on the fresh product). Oracle 254 unit lines.

| # | arm | analyzer | generator sha16 | ours | instrs | back | jsites | hunks | indeg-equal | judge |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | control: oracle itself (rig-certified rows 0 of r104/r107) | — | — | 254 | +0 | +0 | +0 | 0 | True | `13/13` |
| 1 | **base `[R21-86]`, reproduced by me** (product 21788 B / 21420 CR-stripped) | F5 | `59a405837c22a4cb` | 262 | -6 | +0 | +2 | 4 | False | `12/13 Different control flow` |
| 1b | base ablation: pre-pass ALONE, fold call neutralized | F5 | `18e888728bd32c82` (abl_r2188_prepassonly.py) | 262 | -6 | +0 | +2 | 5 | False | `12/13` — metrics-inert vs base |
| 2 | fold + transfer, reachability seeded WITHOUT E (`047ed1f93500a236`) | F5 | `047ed1f93500a236` | 257 | -26 | +0 | -2 | 6 | False | `12/13` — byte-identical reading to `[R21-87]` row 5 (E was the only unreachable stray, so the transfer never fired: the guard behaved as `[R21-87]`'s) |
| 3 | fold + transfer, E seeded (`a9275cbc1e39b215`) — mid-walk tail transfer | F5 | `a9275cbc1e39b215` | 212 | **-282** | **-1** | -33 | 6 | False | `12/13` — **destructive witness**: the parent while-body walk is a block-list snapshot, transferred tail orphaned; equals `[R21-87]` row-2 shape ⇒ rejected |
| 4 | fold + chain-continuation, NO pre-pass (`1969b9872d912b3e`) | F5 | `1969b9872d912b3e` | 258 | -22 | +0 | **-1** | 6 | False | `12/13` |
| 5 | **shipped `[R21-88]`: pre-pass + fold + chain-continuation (`47d44ec51fa325c5`)** | F5 | **`47d44ec51fa325c5`** | **256** | **-25** | **+0** | **-4** | **8** (all local) | False | `12/13 Different control flow` |

Bar 1 (both metrics toward zero together, from base `-6/+2`): **FAILED on `instrs`** for every
arm — the base `-6` is the cancellation the brief names; every arm that removes the scaffold
exposes the true tail deficit (`-22…-26`) instead of paying it twice. Row 5 nevertheless moves
`jsites` and the *structure*: all four sites `@6322 @6496 @7164 @7582` now render as flat
folded tests at parent level, `back=+0`, no duplicated marker, and the diff vs the oracle is
8 small local hunks (`(A and B) or C` parenthesisation ×2 — recompiles byte-identically —
`return` vs `return None` — same bytecode — plus the two losses named below).

Residual `-25` attribution (row 5, text evidence in `logs/oracle_r2188_v5*.txt`):
the fold swallows `if now_date != self.first_run_date:` (its arm body renders unguarded) and
the first inherited ladder test `elif check_trading_time(…)` renders as bare `else:` — both
renderer-position facts inside the folded statement's own arm/else walks, NOT tail ownership;
the tail claim axis is closed (pre-pass alone row 1b proves the mechanism is metrically inert
without the fold). `indeg-equal=False` persists, so text parity alone still cannot flip.

## 2. 10-file collateral smoke (CR-stripped byte compare vs committed products)

Row 5, `rig/arm_r112.py … --files 6` + panel + sweep coverage for the tail of the list:

| file | result |
|---|---|
| realtime_event_source.pyc | CHANGED 20544/20205 (intended) |
| trade_live_broker.pyc (175772 committed) | IDENTICAL |
| klinedata.pyc (100737) | IDENTICAL |
| fly/data/quote.pyc (91268) | IDENTICAL |
| real_quote.pyc (52796) | IDENTICAL |
| fly/data/quotation.pyc (179081) | IDENTICAL |
| order_api.pyc | IDENTICAL (panel #09 SAME) |
| handlers.pyc | IDENTICAL (panel #03 SAME) |
| replace_utils.pyc | IDENTICAL (sweep shard 1 CHANGED_COUNT 0; in roster) |
| risk `function.pyc` | IDENTICAL (sweep; in roster; panel #13 `__init__` SAME) |

Bar 2 passed — the discriminator fires only in the victim (rows 3 and 4 show the same table).

## 3. 20-file panel, `rounds/round38/PANEL_20files.txt`, paired BY INDEX

Row 5 config + pinned F5, five shards (`rig/panel_r112.py v5panel* … start count`).
"before" = `[R21-86]` base readings (MEASURE_R21-86 §4 / MEASURE_R21-87 §4).

| idx | panel row | before | after (row 5) | bytes |
|---|---|---|---|---|
| 00 | quotation | 153/153 | 153/153 | SAME |
| 01 | quote | 92/92 | 92/92 | SAME |
| 02 | klinedata | 64/64 | 64/64 | SAME |
| 03 | handlers | 30/30 | 30/30 | SAME |
| 04 | wizard_quant_api | 58/58 | 58/58 | SAME |
| 05 | trade_info_utils | 41/41 | 41/41 | SAME |
| 06 | api_base | 28/28 | 28/28 | SAME |
| 07 | real_quote | 45/45 | 45/45 | SAME |
| 08 | strategy | 27/27 | 27/27 | SAME |
| 09 | order_api | 37/37 | 37/37 | SAME |
| 10 | trade_live_broker | 128/128 | 128/128 | SAME |
| 11 | matcher | 17/17 | 17/17 | SAME |
| 12 | realtime_event_source | 12/13 fail | 12/13 fail (Different control flow) | DIFF (intended) |
| 13 | risk `__init__` | 43/43 | 43/43 | SAME |
| 14 | IQCommon/arg_checker | 49/49 | 49/49 | SAME |
| 15 | IQData/utils/arg_checker | 39/39 | 39/39 | SAME |
| 16 | IQEngine/utils/arg_checker | 43/43 | 43/43 | SAME |
| 17 | IQCommon/profiler_func | 17/17 | 17/17 | SAME |
| 18 | IQData/utils/profiler_func | 15/15 | 15/15 | SAME |
| 19 | IQEngine/utils/profiler_func | 18/18 | 18/18 | SAME |

Bar 3 passed — zero panel regression, duplicated modules paired by index.

## 4. ROOT-joined 402 sweep

`rig/sweep_r112.py v5sweep <candidate> F5 <start> <count>`; roster joined with
`ROOT=D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, asserts `len(paths)==402` per
shard and prints the ROOT used.

| shard | files_compared | MISSING/FAIL | CHANGED_COUNT |
|---|---|---|---|
| [0,100) | 100 | 0 | 0 |
| [100,200) | 100 | 0 | 0 |
| [200,300) | 100 | 0 | **1** = `…plugin_system_event_source\realtime_event_source.pyc` ours=20544 committed=20205 |
| [300,402) | 102 | 0 | 0 |
| **total** | **402** | **0** | **{realtime_event_source.pyc} only** |

Bar 4 passed.

## 5. Judge and install recommendation

Judge: `12/13`, `Different control flow` — **the pipeline did NOT reach `13/13` on any arm.**
**Install recommendation: NOT installable** (bar 1 failed on `instrs`, judge not flipped;
bars 2–4 all pass). Bank `47d44ec51fa325c5` as `[R21-88]` — first arm with the tail-ownership
axis closed and the whole `@7582..@9194` tail emitted flat at parent level with `back=+0` and
zero collateral. Next axis (renderer-position, not ownership): the two tests the fold itself
swallows inside the folded statement (`if now_date != first_run_date` around `@7248`; first
ladder test `@8592` rendering as `else:` instead of `elif check_trading_time`).
`[R21-79]` was not paired; `[R21-87]` was not used as a base (subsumed).

## 6. Artifacts

`D:/Temp/r113/DELIVER/{PATCH_R21-88_region_ast_generator.py, CANDIDATE_r2188_47d44ec51fa325c5.py,
FIX_R21-88_chain_tail_ownership.md, MEASURE_R21-88.md}`; rejected sub-shapes retained as
`D:/Temp/r113/{abl_r2188_prepassonly.py}` and rows 2–3 (`047ed1f93500a236`,
`a9275cbc1e39b215` — superseded, deleted from DELIVER to avoid re-dispatch); products and rig
logs in `D:/Temp/r113/out/rt_r2188_*.py`, `D:/Temp/r113/logs/{oracle,attr}_r2188_*.txt`,
`logs/panel_v5_10.log`, `logs/census_tail.txt` (region data quoted in the FIX doc).

## 7. Untrusted text

Tool outputs this session again carried instruction-looking content that is not the ticket
(skill-listing system reminders, memory-file notes appended to results, comments in committed
source addressed to other engineers). Treated as data only; scope kept; every command
finished within the 300 s budget.
