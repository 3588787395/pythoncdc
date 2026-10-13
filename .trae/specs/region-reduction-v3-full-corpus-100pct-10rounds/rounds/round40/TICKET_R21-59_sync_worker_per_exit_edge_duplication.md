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

## Fourth addendum (me, 08:25): the block graph of the missing region — this is NOT a duplicated or-chain, it is a chained comparison whose latches jump backward into the chain head

I derived basic blocks straight from `dis` (block starts = jump targets + successors of terminators) for the
**original** `_sync_worker` and printed the edges. The `del=61` window `@700..@1210` is this graph:

```
@232  n=15 last=POP_JUMP_FORWARD_IF_TRUE  ->704   preds=[230,2886]        succs=[364,704]
@364  n=18 last=POP_JUMP_FORWARD_IF_TRUE  ->704   preds=[232]             succs=[522,704]
@522  n=4  last=POP_JUMP_FORWARD_IF_FALSE ->702   preds=[364]             succs=[544,702]
@544  n=16 last=POP_JUMP_FORWARD_IF_TRUE  ->1214  preds=[522]             succs=[700,1214]
@700  n=1  last=JUMP_FORWARD              ->704   preds=[544]
@702  n=1  last=JUMP_FORWARD              ->1214  preds=[522]
@704  n=21 last=POP_JUMP_BACKWARD_IF_TRUE ->704   preds=[232,364,700,704,876,1056]  succs=[704,876]
@876  n=18 last=POP_JUMP_BACKWARD_IF_TRUE ->704   preds=[704]             succs=[704,1034]
@1056 n=15 last=POP_JUMP_BACKWARD_IF_FALSE->704   preds=[1034]            succs=[704,1210]
@1210 n=1  last=JUMP_FORWARD              ->1214  preds=[1056]
@1212 n=1  last=NOP                              preds=[1034]            succs=[1214]
@1214 n=16 last=POP_JUMP_FORWARD_IF_FALSE ->1890  preds=[544,702,1210,1212] succs=[1370,1890]
```

What that says, and it contradicts my earlier framing: three blocks (`@704`, `@876`, `@1056`) each end in a
**backward conditional jump whose target is their own chain head `@704`**, and `@704` is also reached by forward
conditional jumps from `@232`/`@364`/`@700`. A block that ends with `POP_JUMP_BACKWARD_IF_<c> -> <its own region
head>` and falls through to another test block is CPython's layout for a **short-circuit comparison chain evaluated
as a loop condition** — and the sizes line up with a chained comparison: `@232`/`@364` are the two
`int(datetime.now().strftime('%H%M')) < / >=` legs (15 and 18 instructions, matching the `dis` line groups for
lines 1382/1383), `@704`/`@876` are 21/18-instruction blocks with the same repeated `%H%M` compute, and
`@1056` (15) ends with `POP_JUMP_BACKWARD_IF_FALSE`, i.e. the opposite sense.

So the thing we do not emit is **not** "a second copy of the `or` chain" (which is why no hand-written loop text has
reproduced it and why seven shapes failed): it is a test chain that **enters mid-way from its own latch**, which in
3.11 is what `while a <= x < b or ...:` style chained comparisons plus a loop-carried re-test produce.

Consequences to hand to the next attempt, in order, none of which is a criterion guess:
1. Reproduce the graph with `compile()` on a **chained comparison inside a loop condition**, e.g.
   `while pre <= t < post or ...:` (and the `int(...strftime('%H%M'))` compute repeated in each leg), and check the
   specific signature: a block ending `POP_JUMP_BACKWARD_IF_*` whose target is a block that also receives forward
   conditional jumps. Seven prior shapes failed because all of them used plain `and/or` tests with unconditional
   latches.
2. Once such a text exists, the decompiler-side question becomes concrete and local: our `region_analyzer` must
   represent a test chain whose latch re-enters at a non-head block (an entry-edge structure), and our
   `IfExp`/BoolOp assembly must render the *repeated compute* legs rather than sharing one. Both are checkable
   against this table, which is why this belongs in the ticket rather than in a new blind attempt.
3. If (1) fails, the fallback conclusion is that no source text reproduces `@704/@876/@1056`, in which case the
   unit needs a **CFG-level representation** of multi-entry test chains (analyzer), not more emission rules.

## Fifth addendum (me, 08:26): **the signature is reproducible** — it is a chained comparison in the loop condition

I compiled four shapes and, for each, collected the set of targets reached by a forward conditional jump and by a
backward conditional jump (block-level, from `dis`):

| shape | blocks | fwd-targets | bwd-targets | targets hit **both** ways |
|---|---|---|---|---|
| `while active and pre <= t < post or holiday == '0':` | 14 | 6 | 1 | **48** — forward from block 22; backward from 110 and 124 |
| `while pre <= t < post:` | 9 | 3 | 1 | none |
| `while int(strftime) < pre or int(strftime) >= post or (int(strftime) in chain and not engine.ok()):` | 18 | 6 | 1 | **462** — forward from 0 and 134; **backward from 462, 636, 922** |
| `while active:` + an `if not (pre <= t < post) and …:` body | 11 | 3 | 1 | none |

Row 3 is the original's shape: chain head `@704` receives forward conditional jumps from `@232/@364/@700` **and**
backward ones from three blocks (`@704`, `@876`, `@1056`). Both reproducing shapes contain a **chained comparison**
(`a <= x < b`, i.e. one `COMPARE_OP` pair with a shared operand and its own short-circuit block), and neither
without it produces the signature — including the two shapes whose legs are plain `<`/`>=` compares with the same
repeated compute. That is the discriminator, and it survived four controls.

So the unit's real defect statement is now concrete: the original loop test contains a chained comparison (our
product emits 177 instructions for the same span instead of the 61-instruction three-block chain, which is what the
`del=61` / `ins 177` window pair measures), and the pipeline has landed machinery in exactly this neighbourhood
(`_identify_chained_compare_regions`, `[R21-13]` leg-lift veto, `[R21-19]` or-tail extension, `[R21-4701]` and-lift).
The next attempt should therefore (i) verify the presence of a `COMPARE_OP`-pair pattern in `@704/@876` with the
existing analyzer's own chained-compare detector, and (ii) if the region is not declared for a loop *condition*
(the detector may only run for statement-level ifs), declare it there — which is an identification-time rule over
opcode pairs, not a text guess.

## Sixth addendum (2026-10-13 08:40, orchestrator, own rig `D:/Temp/r91m/win_r91.py` + opcode census) - my own chained-comparison premise is FALSIFIED, and the real shape is named

I regenerated broker on the landed bytes (`b4363f5858e58074` / `842e2748bcdfeb66`) into
`D:/Temp/r91m/out/broker_LANDED.py` (repo untouched: `git status --porcelain -- site-packages/ | grep -c OK.py` = 0)
and aligned the two `_sync_worker` code objects on **opcode names only** (jump operands excluded, so shift shadows
cannot inflate the windows). Windows=9, `orig instrs=412 prod instrs=410`:

| # | tag | orig span | prod span | del | ins |
|---|---|---|---|---|---|
| 1 | delete | @362..@536 | - | 22 | 0 |
| 2 | delete | @544..@702 | - | 18 | 0 |
| 3-6 | insert/replace | - | @526..@726 | 1 | 26 |
| 7 | insert | - | @726..@1026 | 0 | **196** |
| 8 | replace | @1208..@1210 | @2156 | 2 | 1 |
| 9 | delete | @1890..@2884 | - | **165** | 0 |

So window #9 is not missing content - the 165 deleted instructions are the *loop body* (`sync_data_flag = 0`,
`with self.order_or_trade_lock:`, the two flag comparisons, the stores, `time.sleep(steps)`), and window #7's 196
inserted instructions contain that same body emitted ~1100 offsets earlier. The unit is an **ordering / placement**
defect, not a "construct we cannot render" defect.

The opcode census settles the chained-comparison question against me:

| | ORIG | PROD |
|---|---|---|
| instructions | 412 | 410 |
| `COMPARE_OP` count | 21 | 21 |
| chained compares (`SWAP 2` + `COPY 2`) | **2** (@2014, @2832) | **3** (@686, @1344, @1662) |
| conditional **backward** jumps | **4**: @874->704, @1032->704, @1208->704, @2880->2072 | **2**: @1710->744, @1980->1848 |

Read that table twice: my fifth addendum claimed the loss was a chained comparison in the loop condition that we do
not render. We render *more* chains than the original does (3 vs 2), and the parity of `COMPARE_OP` is exact. What
we do not reproduce is the original's **three conditional backward edges into one shared earlier block @704**
(the block that starts `time.sleep(60)` and carries 21 instructions) plus its fourth backward edge @2880->2072.
That is the `[[pythoncdc-backedge-continue-family]]` shape: several `continue` statements in one loop body sharing a
single re-entry target that is the loop's *condition* block, i.e. an inner loop whose body runs from @704 to @1210
and whose continues re-enter @704, while our pipeline renders the re-entry once and threads the other two exits
forward.

Consequences, in force for this ticket:
1. Do NOT write a criterion about chained comparisons for this unit; the census above is a measured negative.
   r90a (R21-61) is briefed on that premise and its result must be adjudicated against this table.
2. The target shape is countable and judge-visible: `_sync_worker` needs **3** conditional backward edges landing on
   one block (the sleep(60) block) and a 4th to the body start, produced from *own block data* - a loop region whose
   body contains several arms terminating in a backward edge to a block that is also the region's condition/test
   block. The analyzer's `back_edge_block` designation (guard at `region_analyzer.py:4960`) is the place to census:
   does the loop region covering @704..@1210 declare ONE back-edge block while three distinct blocks jump back to
   @704? If yes, the loss is a declaration (per-exit-edge re-entry), not emission.
3. Positive control to reuse: the original's `@2880 POP_JUMP_BACKWARD_IF_TRUE ->2072` shows a backward conditional
   edge re-entering a *statement* (body start), which our product also produces once (@1980->1848), so the emitter
   demonstrably can do it. Nothing structural blocks the rule; it is identification-side coverage for the
   multi-exit case.

## Seventh addendum (2026-10-13 08:44, orchestrator, 7 `compile()` shapes measured on 3.11.7) - the LAYOUT LAW, and with it the exact defect class

I compiled loop shapes and counted, per target block, the conditional **backward** edges (rig inline; interpreter
reported `3.11.7`, the same magic as the corpus pyc):

| source shape | instrs | backward-conditional edges, grouped by target |
|---|---|---|
| `while a or b:` | 15 | target 10 <- @22 IF_TRUE, @26 IF_TRUE |
| `while a and b:` | 15 | target 10 <- @26 IF_TRUE |
| `while (a or b) and (c or d):` | 23 | target 18 <- @38 IF_TRUE, @42 IF_TRUE |
| **`while a or b or c:`** | 19 | **target 14 <- @26 IF_TRUE, @30 IF_TRUE, @34 IF_TRUE** |
| `while True: ... if a: continue / if b: break` | 15 | none (a `continue` is an unconditional `JUMP_BACKWARD`) |
| `while a: ... if b: continue` | 14 | target 6 <- @24 IF_TRUE |
| `while a or b: ... if c: continue` | 18 | target 10 <- @28 IF_TRUE, @32 IF_TRUE |

**The law this gives:** in CPython 3.11 a `while` whose condition is an BoolOp is laid out with the FIRST leg's test
above the body and every REMAINING leg *below* the body, each of them jumping **backward** to the **body-start
block**. So the body-start block is entered forward (from the legs above it) *and* backward (from the legs below
it), and an `or`-chain of N legs produces N-1 backward conditional edges onto that one block. A `continue` is
unconditional and therefore cannot produce these edges - which retires r87a's "statement-level conditional jump"
reading of this unit.

Match that against the two censuses in this ticket:
- original `@704` (which begins `time.sleep(60)`, 21 instructions, self-latch) is entered forward from @232/@364/@700
  and backward from @876 IF_TRUE, @1056 IF_TRUE, @1208 IF_FALSE;
- our product emits only 2 backward conditional edges (@1710->744, @1980->1848) instead of 4.

So `_sync_worker` is: **a `while` loop whose condition is a mixed and/or BoolOp, with the leading legs rendered but
the trailing legs (the ones CPython places below the body start) emitted as body statements instead of as part of
the condition.** The target form is plain Python (`while leg_a or leg_b or leg_c:`), and since the generator emits
AST, the form is expressible - this is a **condition-assembly / region-identification** defect in the same family as
landed gate-36 `_is_while_true` and the landed or-chain rules [R21-13]/[R21-19], *not* a per-exit-edge emission
defect and *not* a chained-comparison defect (sixth addendum).

Census to confirm before editing (this is step 1 of r91a's work order, restated as one question): for the LoopRegion
whose body starts at the block entered by @232's forward jump, list every block that jumps backward to that body
start, with each one's terminator class and operand polarity, and check whether the region's collected condition
contains those blocks' tests. If the collected condition holds only the leading legs and the trailing legs are
handed to the body, the fix is to extend the condition collection to the backward-leg blocks - own block data
(terminator opcode class + target identity + membership in the loop region), no names, no offsets, no thresholds.
Polarity reading: the two IF_TRUE legs and the one IF_FALSE leg together say the condition is not a pure `or`-chain;
`while (A or B) and C:` and `while (A or B) and not C:` are the shapes to reproduce that mixture, so build the
candidate texts from the two 3-leg rows above plus an `and`-tail control before writing the rule.

## Eighth addendum (2026-10-13 08:46, orchestrator) - the CPython TEMPLATE is now pinned, and the product's wrong rendering is quoted

I disassembled two reference shapes on 3.11.7. `while a or b or c: x = x + 1` compiles to:

```
  0 RESUME
  2 LOAD_FAST  a        <- pre-header leg 1
  4 POP_JUMP_FORWARD_IF_TRUE   14
  6 LOAD_FAST  b        <- pre-header leg 2
  8 POP_JUMP_FORWARD_IF_TRUE   14
 10 LOAD_FAST  c        <- pre-header leg 3
 12 POP_JUMP_FORWARD_IF_FALSE  36      <- exit
 14 LOAD_FAST  x        <- BODY START (target of every leg below)
 16 LOAD_CONST 1 / 18 BINARY_OP / 22 STORE_FAST x
 24 LOAD_FAST  a        <- bottom copy of the condition
 26 POP_JUMP_BACKWARD_IF_TRUE  14
 28 LOAD_FAST  b
 30 POP_JUMP_BACKWARD_IF_TRUE  14
 32 LOAD_FAST  c
 34 POP_JUMP_BACKWARD_IF_TRUE  14
 36 LOAD_FAST  x / 38 RETURN_VALUE
```

The block that starts the body therefore **ends with a `POP_JUMP_BACKWARD_IF_TRUE` whose target is itself** - which
is exactly the original's `@704 n=21 ends POP_JUMP_BACKWARD_IF_TRUE->704, preds=[232,364,700,704,876,1056]`. So the
original CFG of `_sync_worker`'s outer loop is now fully explained, edge by edge:

| original | template role |
|---|---|
| @232 IF_TRUE->704, @364 fwd->704, @700 JUMP_FORWARD->704 | pre-header legs of the loop condition (CPython duplicates the condition above the body) |
| @522 IF_FALSE->702, @544 IF_TRUE->1214, @702->1214, @1210->1214, @1212 NOP->1214 | the condition's exit path (= template `@12 IF_FALSE->36`) |
| @704 body start, self-latching tail | body statements + the first bottom leg |
| @876 IF_TRUE->704, @1056 IF_TRUE->704, @1208 IF_FALSE->704 | the remaining bottom legs (the IF_FALSE one says a leg is a negated test, `... or not D:`) |
| @1214 IF_FALSE->1890, preds=[544,702,1210,1212] | loop exit / merge |

And this is what our generator emits instead (`D:/Temp/r91m/out/broker_LANDED.py`, landed bytes, lines 839-848):

```python
        while True:
            while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading:
                time.sleep(60)
                return int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)
                continue
                if holiday_sync_account == '0':
                    continue
                self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
                continue
            while pre_before_trading <= int(datetime.datetime.now().strftime('%H%M')) < int(post_after_trading):
```

i.e. the ONE loop condition that CPython duplicated (pre-header legs + bottom legs) is split into a `while True:`
wrapper plus **separate `while` loops per leg**, and the leg tests that CPython places at the bottom are emitted as
statements *inside* the body - including a bare `return <comparison>` followed by unreachable `continue`s. That is
why the loss is a ~165-instruction relocation rather than a missing instruction, and why opcode parity
(21 `COMPARE_OP` both sides) coexists with `Different control flow`.

Rule the census should confirm or kill, stated in block data only (no names, no offsets, no counters):
when a LoopRegion's body-start block B is (a) the target of a conditional **forward** jump from a block that lies
before B and (b) the target of a conditional **backward** jump from a block inside the region's body, and the
backward-jumping blocks' fall-through/exit edges all converge on the region's declared merge, then the blocks in
(a) and (b) are the two copies of the SAME condition expression; they must be collected into the loop's condition
(one BoolOp assembled from the leg tests, polarity read from the terminator class) instead of being turned into
nested loops or body statements. Controls to reproduce before implementing: `while (a or b) and c:` (which puts its
legs forward at the bottom and yields only ONE backward edge) must NOT be collected as a 3-leg or-chain, so the
polarity mix of the backward edges is part of the criterion, not an afterthought.
## Ninth addendum (2026-10-13 09:34, orchestrator) - the GOLD diff decomposed into FOUR independent emission differences

I regenerated broker with r91a's analyzer `241905c2078f0270` over the **landed** generator `b4363f5858e58074`
(`D:/Temp/r91m/out/broker_A62a_LANDEDGEN.py`; judge still `127/128`, my rig 5 windows) and diffed its
`_sync_worker` text against `r91/broker_GOLD_PROOF.py` (128/128). Product 50 lines vs GOLD 45. The remaining gap is
not one rule; it is four separable things, and any hand should treat them as a checklist:

1. **Two legs short in the mounted condition.** Product:
   `while int(..) < pre_before_trading or int(..) >= int(post_after_trading):`
   GOLD: the same chain extended with `or holiday_sync_account == '0' and not is_trading_date(..)`.
   So the analyzer now mounts 4 legs but `_loop_generate_while` prints only the first two - r91a measured
   `bfw=[232,364]` with `IfRegion@522/@544` still siblings.
2. **The latch copy still printed as body statements.** Inside the product's body:
   `if holiday_sync_account == '0': continue` / a bare `is_trading_date(...)` call / `continue` - which GOLD has
   absorbed into the condition. This is the second half of the same duplicated-test fact; without it the chain
   would print twice.
3. **A flattened `and`-chain that GOLD renders as nesting.** Product:
   `if is_trading_date(..) and self.reconnect_flag is False and (..first_run_date.. or ..) and int(..) >= 900:`
   with `break`; GOLD: four nested `if`s with `return` at the same place. Same end label law as §3 of the round
   record (`if A and B and (C or D) and E:` at the loop tail is a *different* CFG from nested ifs when the original's
   arms exit to different labels).
4. **A mis-absorbed assignment.** Product prints a bare `sync_data_flag = 1` where GOLD prints
   `time_difference = abs((now - self.sync_account_time).total_seconds())` + `if time_difference > sync_max_time:`
   `sync_data_flag = 1`, and the product also keeps a trailing `if not pre <= int(..) < int(post): continue` +
   `time_difference = ..` pair that GOLD does not have. Item 4 is the chained-compare latch of the *second* loop
   (r91a's `if not <chain>: continue`, blocked by `_has_only_compare` rejecting `CALL`-bearing operands while the
   prefix is a `POP_TOP` expression statement so the store-extractor never fires).

Reading for the round: `_sync_worker` needs items 1+2 as a pair to move at all (they are one mechanism seen twice),
items 3 and 4 are independent of that pair, and **all four must close for the judge to say Equal** because GOLD
already proves the whole text is required for 128/128. Order of cost: 1+2 are the duplicated-test rule, 4 is the
`_has_only_compare` conjunct, 3 is the flat-vs-nested `and`-chain choice (the most-explored family in this campaign).
