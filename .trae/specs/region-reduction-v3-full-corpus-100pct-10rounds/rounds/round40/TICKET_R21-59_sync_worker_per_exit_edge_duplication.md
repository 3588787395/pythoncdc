# TICKET_R21-59 — `_sync_worker`: the gap is CPython's per-exit-edge duplication of the loop-condition legs, not a polarity or a missing statement

Written by the orchestrator from my own measurement, 2026-10-13 08:01 (container clock).
Unit: `<module>.TradeLiveBroker._sync_worker`, `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
(file 127/128; flipping it is corpus 6615→6616 and the last broker unit).
Base: landed bytes generator `b4363f5858e58074` / analyzer `842e2748bcdfeb66`. My `unit_diff`: `orig=404 prod=401
delta=-3`, 5 windows, 6 landings. r87a's §0 shows `delta=-3` is the **net of +221 inserted against −224 deleted**.

## What I measured this turn

Grouped the original's instructions by `co_lines()` source line (412 instructions, 55 line-groups; I used line
numbers only as *diagnostic* grouping — a criterion on line numbers would violate the spec). The loop body is
lines 1382–1386 and its condition legs appear **twice**:

```
line 1382 n=15 … end=POP_JUMP_FORWARD_IF_TRUE  ->704      line 1382 n=15 … end=POP_JUMP_BACKWARD_IF_TRUE ->704
line 1383 n=18 … end=POP_JUMP_FORWARD_IF_TRUE  ->704      line 1383 n=18 … end=POP_JUMP_BACKWARD_IF_TRUE ->704
line 1385 n=4  holiday_sync=='0'  IF_FALSE ->702         line 1385 n=4  … IF_FALSE ->1212
line 1384 n=14 is_trading_date(...) CALL                 line 1384 n=14 is_trading_date(...) CALL
line 1385 n=4  … IF_TRUE ->1214, JUMP_FORWARD            line 1385 n=3  IF_FALSE->…, JUMP_FORWARD, NOP
line 1386 n=6  <call>(60) POP_TOP        <- the sleep statement (the loop body)
```

i.e. the compound test `if (A or B or (C and D))` inside `while True:` is **compiled per exit edge**: one copy of
the leg chain whose failures jump forward to the exit, and a second copy whose failures fall into the backward
re-entry. That is exactly the family already documented for `handlers._target` (CPython duplicates the shared test
legs for each loop exit, so a single flat `while <BoolOp>:` rendering cannot reproduce the CFG, and no
identifier-only rule can manufacture the second copy either).

## Consequences for the next attempt (read before dispatching anything)

1. Do not chase window #1's `POP_JUMP_FORWARD_IF_TRUE` vs our `IF_FALSE`: with duplicated legs, "which polarity" is
   the wrong question, which is why r71a's and r79a's seven candidates all left the unit `Different control flow`.
2. The honest shape this unit needs is a **two-copy rendering of the condition chain**: the second copy is what our
   product is missing (the `del=61 @700..@1210` and `del=162 @1890..@2884` windows). Any candidate that reduces
   `delta` by moving statements around, without producing the second leg chain, will still judge
   `Different control flow` — today proved that fourteen times on the sibling unit.
3. Before writing a criterion, run the two-candidate `compile()` experiment on the WHOLE module: try
   (a) `while True: if (A or B or (C and D)): body; more` and (b) the same split into two sequential tests, and
   compare `co_code` + resolved jump targets against the original's 412 instructions. If neither shape reproduces
   the doubled legs, the unit is expressible only via the loop-exit duplication mechanism, and that mechanism is
   the ticket — not this unit.
4. Precedent to mine: the landed `[R21-13]` leg-lift veto, `[R21-19]` `_r2119_or_tail_extension` /
   `_r4701_and_lift_or_tail`, and `[R21-55]`'s diamond-join recovery all changed **condition assembly** for
   similar shapes; the duplication question is the one none of them touched.

## Acceptance bar (unchanged)

`_sync_worker` judged Equal ⇒ broker **128/128** (that also makes it a whole-file green ⇒ 401/402 files), with the
new corpus-wide pre-install sweep (regen all 402, CR-stripped byte-diff vs `git archive HEAD`, judge only changed
files) and `clock_worker 12/13` + canaries (`quotation 153/153`, `quote 92/92`, `replace_utils 9/9`,
`realtime_event_source 13/13` if the other ticket landed first) never decreasing.

## Closed axes on this unit (do not re-run)

r71a's `_r2144_detect_while_condition_nested_or_and` (census FIRES=1, inert because `analyze()`'s
`block_to_region` priority rebuild at `region_analyzer.py:1871`/`:4119` reclaims blocks 232/364/522/544 to the
enclosing `while True` LoopRegion; forced retention leaks `while False: pass` and worsens `delta -3 → +19`), and
all seven of r79a's reclaim-guard / back-edge candidates — I judged every one: `_sync_worker` reads
`Different control flow` in all seven (adjudication §16). r87a also proved the just-landed [R21-55]/[R21-56]
machinery has **zero evaluations** inside this code object (§17), and that three hand-written "ideal" loop texts
(`+68 / +19 / -71`) still judge `Different control flow`.
