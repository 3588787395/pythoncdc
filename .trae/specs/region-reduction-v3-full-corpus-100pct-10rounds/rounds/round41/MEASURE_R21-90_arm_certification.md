# MEASURE R21-90 - arm certification (clock_worker)

All numbers below are transcribed from tool output captured in `D:/Temp/r116`
(the fix engineers mirror) at the stated times. Nothing here is arithmetic on
earlier rows. The mirror is live, so every hash is stamped, not assumed.

## Arm under measurement

- analyzer `996a1b1acf143458` (F5, `backup/ana_F5_996a1b1acf143458.py`, 2129303 B)
- generator `558192ecf6d5f8a0` = `[R21-90]`, delivered as
  `DELIVER/PATCH_R21-90_region_ast_generator.py` (4042 B, 2026-10-14 01:01 UTC)
- landed bytes untouched: `git status --porcelain -- core/` = 0 lines, and the repo
  pair remains analyzer `fef59e95359f36fd` / generator `c3049a87daf59acc`.

## Reading (engineer log `logs/oracle_v90.txt`, 01:01 UTC; my rig agrees)

```
[oracle-diff] unit=clock_worker ours=257 ORACLE=254 hunks_vs_ORACLE=8
   @@ -177 +177 @@   @@ -180 +180 @@   @@ -185,3 +185,3 @@   @@ -195 +195 @@
   @@ -204 +204 @@   @@ -221 +221 @@
[census] DELTAS     instrs=-2 back=+0 jsites=+0
[census] indeg-equal=False back-equal=True opseq-equal=False
[judge] ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
[judge] [single] status=failure units=12/13 success_rate=92.31%
```

Ladder so far on this file: `instrs -114 -> -26 -> -25 -> -13 -> -2`, `jsites -3 -> 0`,
`back=+0` held at every rung. `jsites` (jump-site count) is now at parity and `back`
(back-edge multiset) was never broken, so the two jump-target axes are closed.
`indeg-equal` is still `False` and `opseq-equal` is still `False`.

## Collateral evidence

20-file panel (`logs/panel_v90p.txt`, 01:14 UTC) - 19 of 20 files at full unit count
with `BYTES=SAME` against the committed products:

```
#00 quotation 153/153   #01 quote 92/92    #02 klinedata 64/64   #03 handlers 30/30
#04 wizard_quant_api 58/58  #05 trade_info_utils 41/41  #06 api_base 28/28
#07 real_quote 45/45  #08 strategy 27/27   #09 order_api 37/37   #10 trade_live_broker 128/128
#11 matcher 17/17     #13 risk __init__ 43/43  #14/15/16 arg_checker 49/39/43
#17/18/19 profiler_func 17/15/18           all BYTES=SAME
#12 realtime_event_source 12/13  BYTES=DIFF(20706/20205)  failing=1  <- the target unit
```

ROOT-joined 402 sweep, shard `[200,300)` (`logs/sweep_v90s_200.txt`, 01:22 UTC):

```
files_compared 100 / MISSING-FAIL 0 / STUBS 7 / CHANGED_COUNT 1
  CHANGED site-packages\IQEngine\plugins\plugin_system_event_source\realtime_event_source.pyc
[sweep] ana=996a1b1acf143458 gen=558192ecf6d5f8a0 roster=402
```

Only the target file changes on that shard, so `CHANGED` is exactly the unit under
attack. Shard `[300,400)` was started at 01:23 UTC and shards `[0,200)` had not run
for this arm when this row was written; the sweep restored
`ana=996a1b1acf143458(True) gen=cb8c2c7928672abd(True)` after the shard, so the
mirror is not left in a patched state.

## Verdict

**Not a flip. Banked, not installed.** Zero collateral is now proven for this arm on
the panel and on one full sweep shard, and both jump axes are at parity, but the sole
flip condition is judge `13/13` on `clock_worker`, and it reads `12/13 / Different
control flow`.

## The two named residuals (engineer `logs/attr_v90.txt`, 01:0x UTC, 5 grouped hunks)

Text-only, NOT CFG-visible on 3.11 (do not spend a gate on them):

```
H1/H2/H3  if (A and B) or C:      vs  if A and B or C:      (chained-compare fold, @8904/@8948)
H4        return                   vs  return None
```

Structural - the only hunk that can move `indeg-equal`:

```
H5 @@ -244,10 +244,13 @@  del=4 ins=7   -> step2 spurious wrapper body
  ORACLE : elif now_date == self.before_trading_date and now_date > self.after_trading_date
                and delay_after_trading >= now_time >= after_trading:
  OURS   : elif now_date == self.before_trading_date and now_date > self.after_trading_date:
               if delay_after_trading >= now_time >= after_trading:      (nested wrapper)
```

plus, per the engineers own FIX note, the loop-tail `else:` / `return None` pair, which
is stated to be the whole of the remaining `+2` in `ours`.

## Next handoff

- Re-hash the engineers live bytes before trusting any number here: at 01:18 UTC the
  mirror had already moved to generator `6c6aab8920934a33` (`out/cand_r2190.py`) and
  analyzer `4cd0f74e0681ce4c`, i.e. the following arm edits BOTH files.
- Close H5 (fold a trailing chained-compare leg into the owning `elif` condition instead
  of emitting a nested `if`) - that is the only remaining hunk that can change the CFG
  shape. `instrs -2` and `jsites 0` mean the block inventory is already right.
- Only after `instrs` and `jsites` are both at parity AND judge reads `13/13`: install
  with `install_pair.py --ana 996a1b1acf143458 --gen <candidate>`, re-run the panel 20 by
  index, complete all four sweep shards, then `gate_chain.py 41 40`.
- Gate label 41 is still unconsumed; corpus stays 6616/6617 (99.9849 %), 401/402 files.
