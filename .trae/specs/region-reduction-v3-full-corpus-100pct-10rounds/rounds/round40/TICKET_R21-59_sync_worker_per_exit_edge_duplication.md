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

## Addendum (me 2026-10-13 08:04): the first experiment is already run, and it is negative

I compiled the two obvious shapes on 3.11.7 and counted conditional-jump kinds in the extracted function:

| shape | instructions | `%H%M` loads | conditional jumps |
|---|---|---|---|
| A `while True:` + one flat `if A or B or (C and D):` body | 57 | 2 | `POP_JUMP_FORWARD_IF_TRUE` ×4, `POP_JUMP_FORWARD_IF_FALSE` ×1 |
| B same test split into `_a=…; if _a: continue; _b=…; if _b: continue; if C and D:` | 63 | 2 | `POP_JUMP_FORWARD_IF_TRUE` ×2, `POP_JUMP_FORWARD_IF_FALSE` ×3 |

**Neither emits a single `POP_JUMP_BACKWARD_IF_*`,** while the original contains
`POP_JUMP_BACKWARD_IF_TRUE ->704` and `POP_JUMP_BACKWARD_IF_FALSE ->1212` in its second leg copy. Backward
conditional jumps appear only when a path enters the chain *mid-way* with its remaining targets lying behind it, so
the original's second copy is not produced by any shape I can obtain from a plain `while`/`continue`
re-arrangement. Combined with r87a's three hand-written ideal loop texts (`+68 / +19 / -71`, all still
`Different control flow`), the honest state is: **four independent text shapes have failed to reproduce the doubled
legs**, which is evidence that the gap is a CFG-level duplication our pipeline does not currently generate at all.

Therefore the ticket's decision rule stands and is now sharpened: whoever takes this unit must first produce a
`compile()`-reproducible shape for the doubled legs (a text whose extracted function contains both a
`POP_JUMP_FORWARD_IF_TRUE ->X` and a `POP_JUMP_BACKWARD_IF_TRUE ->X` for the same `X`), and only *then* look for an
identification-time rule that renders it. If no such text exists, the correct conclusion is that `_sync_worker`
needs a jump-threading/duplication capability in the emitter, and that is an architecture task, not a criterion.

## Second addendum (me, 2026-10-13 08:22): my "missing duplication capability" claim is UNSUPPORTED, and the shape is corpus-unique

I scanned the whole corpus (all 402 gate rows, every nested code object except each file's module-level object,
6215 objects) for conditional-jump kinds:

* **217 of those code objects contain `POP_JUMP_BACKWARD_IF_*` and are currently judged Equal** (216 excluding
  `_sync_worker` itself, which the scan also counts). So the emitter produces backward conditional jumps
  routinely — my addendum-1 conclusion that this unit needs a *new capability* was wrong, and it is withdrawn.
  My first pass of this scan also mis-counted "failing: 0": the report stores failures as the whole line
  `***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow`, so a `endswith('.'+co_name)` test
  never fires. The two failing units are exactly those two lines, and the gate's own reading stands
  (6615/6617, 400/402 files).
* The signature I actually care about — **one target receiving BOTH a forward and a backward conditional jump in the
  same code object** — occurs in **exactly one unit in the entire corpus: `_sync_worker`** (targets `[704]`,
  20 forward vs 3 backward conditional jumps). No positive control exists anywhere else.

What that changes for the next hand: the question is no longer "can we duplicate legs?" but "what source construct
makes CPython thread the *same* test chain twice with one copy entering from the latch?" — because no other unit in
the corpus needed it, and 216 units already prove backward legs per se are fine. Two concrete probes, both cheap and
neither a criterion-guess: (i) `compile()` a handful of whole-module variants where the loop test is also evaluated
once *before* the loop (a pre-test plus `while <re-test>:`), which is the classic way a latch enters mid-chain; and
(ii) re-read the original's `@700..@1210` region (the `del=61` window) for a second *entry point* into the chain
rather than a literal duplication — if that region is an entry, the fix is a CFG/ownership matter, not a text matter.

## Third addendum (me, 08:24): seven source shapes now known NOT to produce the signature — start from this list

I compiled four more whole-module variants and scored them the same way (sets of forward- vs backward-conditional
jump targets inside the extracted function):

| shape | fwd cond jumps | bwd cond jumps | same-target both |
|---|---|---|---|
| pre-test then two `while active:` branches | 6 | 2 | **none** |
| flag assigned before loop, re-assigned at the end of the body | 2 | 1 | none |
| `while active:` + one `if <or-chain>:` body | 5 | 1 | none |
| `while active:` with two `continue` guards then an `if C and D:` | 5 | 1 | none |

Together with r87a's three hand-composed ideal loop texts (`+68 / +19 / -71`), **seven shapes are now eliminated**.
What the signature requires, read off the original: block `704` is reached by a *forward* conditional jump from legs
at low offsets and by a *backward* conditional jump from legs at higher offsets, i.e. the same test chain is entered
from two places and one entry begins mid-chain. So the search is not "a text that duplicates a chain" but
"a text whose *latch* is a conditional jump into the middle of the chain" — which is why `continue`-style variants
above (whose latch is unconditional) cannot produce it. Treat this as the constraint, and if a next attempt cannot
name such a construct, the honest verdict is that `_sync_worker` needs the CFG to expose a second entry edge rather
than a new source text — an analyzer/emission ownership question, and the `del=61` window `@700..@1210` is where to
look for it (that region is the one the scan flags as absent from our product).
