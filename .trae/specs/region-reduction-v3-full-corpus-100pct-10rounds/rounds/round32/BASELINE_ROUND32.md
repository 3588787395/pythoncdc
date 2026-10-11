# Round-32 baseline (measured 01:38 from the gate-31 sealed products, `unit_diff <rel.pyc> <co> --prod <abs OK.py> --all`)

口径: products as regenerated in place by gate 31 (`regen ok=402 bad=0`), so no `--source` was needed —
nothing here judges a patch. Sealed bytes: generator `37d9fecb893704ac`, analyzer `35e227ac3e7b25af`.
Corpus **6606/6617 units (99.8338%), 397/402 files, 11 residual units in 5 files** (`RESIDUAL_ROUND31.md`,
`UNREGISTERED 行数=0`).

| file | unit | len orig/prod | delta | hunks | landings | vs gate-31-round baseline (`BASELINE_ROUND31.md`) |
|---|---|---|---|---|---|---|
| `IQCommon/logger/handlers.pyc` (29/30) | `_target` | 199 / 195 | −4 | 1 | 4 | unchanged |
| `IQCommon/util/trade_info_utils.pyc` (40/41) | `kill_trade_process` | 659 / 659 | 0 | **0** | 2 | unchanged (two identical `return None` tails, exits swapped) |
| `fly/data/quote.pyc` (91/92) | `run_individual_transform` | 407 / 355 | −52 | 10 | 3 | unchanged (r46a's banked analyzer half would read −3 → `0/2/2`, still 91/92) |
| `…/realtime_event_source.pyc` (12/13) | `clock_worker` | 1424 / 1311 | **−113** | 7 | 18 | unchanged |
| `…/trade_live_broker.pyc` (121/128) | `_process_order` | 507 / 42 | −465 | 4 | 1 | unchanged |
| ″ | `_process_cancel_order` | 333 / 40 | −293 | 3 | 0 | unchanged |
| ″ | `_sync_worker` | 404 / 401 | −3 | 5 | 6 | unchanged |
| ″ | `_trade_status_handle` | 127 / 124 | −3 | 3 | 2 | unchanged |
| ″ | `etf_purchase_redemption` | 426 / 414 | −12 | 5 | 0 | unchanged |
| ″ | `ipo_stocks_order` | 1181 / 1180 | −1 | 1 | 3 | unchanged |
| ″ | `get_ipo_stocks` | 481 / 481 | 0 | **0** | 1 | unchanged (narrowest residual in the corpus) |

Every row is `judge_diff=True`. **No residual shape moved when gate 31 landed** — unlike gate 30, whose
`handlers` row went `−2/1/3 → −4/1/4` while its count stayed 29/30. That check is now mandatory after every
gate, because a count-only witness hides exactly this class of damage.

## Dispatch map (five engineers, round 32)

| slot | ticket | file owned | unit(s) | bar |
|---|---|---|---|---|
| r50a | `rounds/round31/TICKET_R21-26_handlers_criterion_over_fires_canaries.md` | generator | `handlers._target` | 30/30 **and** `arg_checker` 49/49, `profiler_func` 17/17 in all three packages |
| r51a | clock_worker **M2** (analyzer labels its own region entry @6690 as BREAK) | analyzer | `clock_worker` | its −17/+17 hunk closed, necessary, zero regressions; `MEASURED CO-REQUISITE PARTIAL` allowed |
| r52a | clock_worker **M1** (`_r23_or_*` bulk-claims `else_blocks` incl. 7 never-dispatched child entries) | generator | `clock_worker` | its −109 hunk closed, necessary, zero regressions; same partial rule |
| r53a | `TICKET_R21-25` (`kill_trade_process` tail-allocation order) | generator | `kill_trade_process` | 40/41 → **41/41** file flip |
| r54a | broker `get_ipo_stocks` (`landings=1`, TARGET_ONLY) | generator | `get_ipo_stocks` | broker 121 → **122/128** unit flip |

`clock_worker` needs M1+M2+M3 all closed, so r51a and r52a are explicitly not expected to flip it alone;
M3 is held back until I can measure the merged pair. Broker keeps 6 further mechanisms queued
(`Task #75`) — 7 units, 7 mechanisms, no single criterion flips the file.

## Rig changes this round

- Pre-gate panel is **20 files** (`D:/Temp/t30/panel14.py <root> <tag> 0 20`): the 14 residual/landed files
  plus the six duplicated-module canaries (`arg_checker` ×3 = 49/39/43, `profiler_func` ×3 = 17/15/18).
  `0 14` no longer covers the canaries — passing the wrong count is how a −6-unit merge nearly landed.
- `D:/Temp/t31_hunkpick.py`: applies a SUBSET of one candidate's hunks onto a moved base by content anchors
  (asserts a unique anchor hit and that any replaced line still matches). This is what attributed gate 31's
  regression to h2 rather than to the narrowing hunks.
- `D:/Temp/t30/mkmix.py` still merges whole candidates by base coordinates and asserts non-overlap.

## Mid-flight trend reads (02:17–02:22) — NOT verdicts

Measured on the engineers' live mirror files, which were still being edited; a moving hash is never a
verdict, and each DELIVER will be re-measured from scratch in my own mirror before anything is installed.

| build | measurement | reading |
|---|---|---|
| r50a `d677077be490f11b` | handlers **30/30**, arg_checker **48/49**, profiler_func **16/17** | the flip works on the current bytes, but the canary narrowing is not in place yet — this is exactly the gap R21-26 was written for |
| r52a `01970a924b74afb4` | clock_worker `−113 → −10`, hunks 7→8, landings 18→14 | M1's bulk-claim guard is closing the −109 skip almost entirely (−10 left); note hunks ROSE by 1 and landings fell by 4, so the residual is no longer the skip — consistent with M2/M3 owning what remains, and still zero flips |
| r51a `36dea812a1f9c180` | clock_worker `−113 → −122`; quote `−52/10/3` unchanged; `_sync_worker −3/5/6` unchanged | see `NOTE_R21-31`: M2's current build worsens its own unit and does not touch the other two, so the three-unit family claim is dead |

Both adjudication mirrors (`D:/Temp/r30chk`, `D:/Temp/r30chkB`) are re-seeded from the repo's sealed bytes
after these reads, and note for future runs: those mirrors have no `site-packages`, so `unit_diff.py` must be
given the **absolute** pyc path there — the relative form resolves against `ROOT/site-packages` and dies,
which is what made two of my earlier loops print nothing.
