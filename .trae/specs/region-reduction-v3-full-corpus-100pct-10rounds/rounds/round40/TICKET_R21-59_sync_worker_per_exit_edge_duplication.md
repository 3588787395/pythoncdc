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
## Tenth addendum (2026-10-13 09:38, orchestrator) - items 3 and 4 corrected against the ORIGINAL's own bytecode

I enumerated every `RETURN_VALUE` in the original `_sync_worker` and disassembled the reconnect / `time_difference`
region. Two of my ninth-addendum readings need correcting, and the corrections make both items cheaper than they
looked.

**(a) There is exactly ONE `RETURN_VALUE` in the whole unit, at `@1874`, and its context is the reconnect call:**

```
@1850 LOAD_GLOBAL datetime ... @1862/@1874:  LOAD_ATTR trade_id | PRECALL 2 | CALL 2
                                             | POP_JUMP_FORWARD_IF_TRUE 1876 | LOAD_CONST None | RETURN_VALUE
```

i.e. the original is `if not reconnect(self.broker.trade_account, self.trade_id): return` - the ONLY return in the
function, sitting at the end of the reconnect region `@1214..@1890` (which is why `@1214`'s false exit jumps to
`@1890`, the second loop's body, while its true side falls through the reconnect statements). The landed product
emits `break` there instead. So item 3 is **not** a flat-vs-nested `and`-chain question at root: it is a
**terminator-class mis-declaration** - the arm's terminal opcode is a `RETURN_VALUE` in the original and is rendered
as a loop exit. (The flat-vs-nested difference in my ninth addendum is a consequence of the same region: GOLD nests
precisely so the `return` sits at that depth.) This belongs to the `return None` vs break/continue terminator family
already documented for other units, not to the elif end-label law.

**(b) The `time_difference` pair is exactly where the original says it is, and there are TWO `sync_data_flag = 1`
assignments to keep apart:**

```
@2350 STORE_FAST time_difference                <- time_difference = abs((now - self.sync_account_time).total_seconds())
@2352 LOAD_FAST  time_difference     (line 1422)
@2354 LOAD_GLOBAL sync_max_time
@2366 COMPARE_OP >
@2372 POP_JUMP_FORWARD_IF_FALSE 2378
@2374 LOAD_CONST 1 -> @2376 STORE_FAST sync_data_flag   (line 1423)   <- the SECOND one, guarded
@2378 LOAD_FAST sync_data_flag     (line 1425)
@2380 POP_JUMP_FORWARD_IF_FALSE 2492            <- if sync_data_flag: sync_account() ...
```

and the FIRST `sync_data_flag = 1` is at `@2136..@2138 (line 1415)`, inside
`if receive_order_response_flag == 1 or receive_trade_response_flag == 1:` (the `or` at `@2112/@2134`), right after
`sync_data_flag = 0` at `@2072`. So the product's bare unguarded `sync_data_flag = 1` is the **line-1423** site with
its `if time_difference > sync_max_time:` test lost, and the line-1415 site is emitted correctly - the two are not
the same statement, which is the trap I nearly set for the next hand in addendum 9 (I described the missing
`time_difference = abs(...)` as being *printed elsewhere*; it is actually printed at the **wrong position**: the
product computes it at the second loop's tail, after `time.sleep(steps)`, while the original computes it at `@2214
..@2350`, before the guard).

**(c) Consequence for the round's division of labour.** Four separable mechanisms now have owners and none of them is
"the unit needs a new construct":

| item | mechanism | owner |
|---|---|---|
| 1 | mounted 4-leg while chain prints only 2 legs | r93a (analyzer) / r94a (generator) |
| 2 | latch copy printed as body statements | r93a / r94a |
| 3 | reconnect arm's terminal `RETURN_VALUE` rendered as a loop exit | unowned → dispatched as R21-67 |
| 4 | `if time_difference > sync_max_time:` guard lost and its `abs(...)` compute misplaced | r95a |

`_sync_worker` therefore needs items 1+2+3+4 together to read Equal, which GOLD already proves is a sufficient text
(128/128) and which my `return`/`sync_data_flag` measurements above show is a *necessary* one too: each of the four
differences is individually visible in the original's instruction stream.
## Eleventh addendum (2026-10-13 09:44, orchestrator) - CORRECTION to my own addenda 9/10: the SECOND loop is the same duplicated-test shape, so the four items collapse into THREE mechanisms

I traced every edge into the second loop's body start and disassembled both chained-compare clusters. The original
contains **two** duplicated tests, not one:

| | entry copy (above the body) | latch copy (below the body) |
|---|---|---|
| loop 1, `while A or B or (C and not D):` body start `@704` | `@232/@364/@700` conditional jumps **forward** into `@704`; `@522/@544/@702` to the exit | `@704` own tail `POP_JUMP_BACKWARD_IF_TRUE 704`, `@876` same, `@1056/@1208` `IF_FALSE 704` |
| loop 2, `while pre_before_trading <= int(strftime) < int(post_after_trading):` body start `@2072` | `@2014 SWAP 2 / @2016 COPY 2 / @2018 COMPARE_OP <= / @2024 IF_FALSE 2066` then `@2054 COMPARE_OP < / @2062 IF_FALSE 2886 / @2064 JUMP_FORWARD 2072` | `@2832 SWAP 2 / @2834 COPY 2 / @2836 COMPARE_OP <= / @2842 IF_FALSE 2884` then `@2872 COMPARE_OP < / @2880 POP_JUMP_BACKWARD_IF_TRUE 2072 / @2882 JUMP_FORWARD 2886` |

and the only two edges into `@2072` are `@2064 JUMP_FORWARD` (entry) and `@2880 POP_JUMP_BACKWARD_IF_TRUE` (latch),
with both copies' false legs landing on `@2886` (`time.sleep(steps)`, then `@2928 JUMP_BACKWARD 232`).

Consequences, correcting what I wrote an hour ago:
1. **My "item 4" was half-mislabeled.** The product's `if not pre_before_trading <= int(strftime) < int(post):
   continue` at the second loop's tail is **not** a separate chained-compare problem: it is the *latch copy* of loop
   2's condition, i.e. the same mechanism as items 1 and 2. Any rule that handles only loop 1 will leave loop 2's
   garbage in place and the unit will still read `Different control flow`.
2. The remaining, genuinely separate part of old item 4 is **statement-sequence ownership**: the original computes
   `time_difference = abs(...)` at `@2214..@2350`, guards `@2352 LOAD_FAST time_difference / @2354 LOAD_GLOBAL
   sync_max_time / @2366 COMPARE_OP > / @2372 POP_JUMP_FORWARD_IF_FALSE 2378`, and stores `sync_data_flag = 1` at
   `@2374/@2376` **under** that guard; the product emits an unguarded `sync_data_flag = 1` and relocates the compute
   to after `time.sleep(steps)`. Note the *legitimate* second `sync_data_flag = 1` at `@2136` (line 1415, inside the
   `receive_order_response_flag == 1 or receive_trade_response_flag == 1` test) is emitted correctly - the two sites
   must not be conflated.
3. So the honest decomposition is **three** mechanisms: **(A)** duplicated while-test (loops 1 and 2: fold the entry
   legs into the region's condition AND drop the latch legs from the body sequence), **(B)** the `time_difference`
   guard/assignment ownership, **(C)** the reconnect arm's terminal `RETURN_VALUE` (`@1874`, the unit's only one)
   rendered as `break`. Owners: A = r93a/r94a (and, per this addendum, their rule must cover loop 2's chained
   compare too, not just the or-chain), B = r95a, C = r96a.
4. This matches r91a's independent observation that `@1890`'s chained compare is *detected but not declared* while
   its latch copy `@2668` *is* declared as `IfRegion@2668` - "the mirror image of the same duplication disease in
   the second loop". Two engineers and I now agree the second loop is the same axis; treat any A-side candidate
   that leaves `@2832..@2884` rendered as body statements as incomplete, and measure loop 2 explicitly before
   declaring A done.
## Twelfth addendum (2026-10-13 09:48, orchestrator) - a RESIDENT 40-second acceptance harness for this axis already exists, and its baseline is 8 RED

Task #38 (`R14-02: or-chain with chained-compare tail`) from round 14 was the same family, and its battery is still
in the repo and still running:
`python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/repro/run_repro.py`
(compile each source with the 3.11 interpreter, decompile **the .pyc** through the pipeline, judge only pycdc
products - judging a hand-written source against itself is vacuous, as that battery's own docstring says).

Baseline I measured on the landed bytes just now, in 40 seconds:

```
r01_or_cc_return.py   success units=2/2        <- green today, was RED in round 14
v1_while_try_cont.py  failure units=1/2
v2_if_only_cont.py    failure units=1/2
v3_try_no_while.py    failure units=1/2
v4_cc_in_middle.py    failure units=1/2
v5_two_elif_cc.py     failure units=1/2
v6_guard_clause.py    failure units=1/2
v7_ccarm_as_elif.py   failure units=1/2
v8_two_cc_arms.py     failure units=1/2
RED=8 / 9
```

Why this matters for round 40, and how to use it:
1. It is a **second, much cheaper discriminator than the corpus sweep** (40 s vs ~190 s) that exercises exactly the
   shapes this unit is made of: `while` + `continue` + a chained-compare or `or`-chain tail (`v1`, `v4`, `v7`, `v8`).
   Run it on every candidate before asking for a sweep.
2. Round 14's own conclusion was "condition text becomes correct; remaining blocker = parent IfRegion condition
   assembly … root shared with #39: **Phase 2 chained-compare regions steal boolop-chain membership**" - which is the
   same steal I measured today as `_detect_while_condition_boolop_chain(@232)` returning length 1 and
   `interrupts_boolop_forward_chain` vetoing `@364`. So this is not a fresh axis with no history; it is round 14's
   unfinished one, and any fix should be judged against those 8 reds, not only against `_sync_worker`.
3. Reverse use, as an over-fit test: a candidate that flips `_sync_worker` while leaving all 8 battery reds red is
   suspicious - it would mean the rule fires on exactly one CFG in the corpus (which is plausible here: predicate P
   fires 1 of 173 loop conditions) and must be defended by the panel and the sweep, not by generality claims.
   Conversely any battery red turning GREEN is evidence of a real generalization and should be reported.
4. The corpus has **exactly one** `while` statement whose test contains a chained comparison in any committed
   product - `trade_live_brokerOK.py:848`, inside this very unit (grep of `while …<=…<…:` over all 402 `*OK.py`).
   So there is no green positive control for the shape: nothing else in the corpus proves we can render a duplicated
   `while`-test with a chained compare, which is why GOLD had to be built by hand.
Reading after installing that battery in my mirror at the correct depth (`D:/Temp/r91m/.trae/.../round14/repro`, so
`ROOT` resolves to the mirror): r91a's analyzer candidate `241905c2078f0270` leaves the battery at **RED=8/9, byte for
byte the landed reading** - mounting the chain in `_sync_worker` does not reach any of the eight synthetic shapes. So
the chain-mount half is not yet a generalization, and a candidate's battery score is now a required column in its
halves table (baseline to beat: RED=8/9 with `r01_or_cc_return` green).
## Thirteenth addendum (2026-10-13 09:52, orchestrator) - CORRECTION to my own twelfth addendum: those 8 battery reds are a NEIGHBOURING axis, not a repro of mechanism A

I read three of the battery sources before relying on that claim. All nine cases are `while True:` + `try:` wrapping an
**`if/elif` chain whose arms are or-chains ending in a chained comparison**, e.g. `v1_while_try_cont.py`:

```python
while True:
    try:
        if dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':
            time.sleep(60); continue
        elif '08:30:00' <= dt_strf < '08:59:00':
            time.sleep(30); continue
        break
    except Exception:
        pass
```

So the test sits in an `IfRegion`, not in a `LoopRegion` condition, and CPython's duplicated-*while*-test layout is not
what these cases exercise. My twelfth addendum therefore overstated the harness: the corrected statement is

* **The battery is a NO-REGRESSION witness for this axis**, not its acceptance test: any mechanism-A candidate must
  leave `RED=8/9 (r01_or_cc_return green)` unchanged or better, and a candidate that *increases* the red count is
  collateral damage caught in 40 seconds rather than 190.
* **Mechanism A's own acceptance repros are the two built this round**: r90a's `repro_rotated_while.pyc`
  (`rounds/round40/r90/repro/`, judged `units=1/2 Different control flow`, a 12-line function that reproduces the
  garbage in kind) and r91a's `true_source_sync_worker.py` / `broker_GOLD_PROOF.py` (128/128).
* Round 14's conclusion quoted in addendum 12 ("Phase 2 chained-compare regions steal boolop-chain membership; the
  blocker is parent **IfRegion** condition assembly") is about the `if/elif` family, which is a *sibling* of the
  `while` family I mapped today: same steal mechanism, different owning region. The shared root is worth one
  sentence in each ticket, but a fix for one does not buy the other, and I should not have implied it did.
## Fourteenth addendum (2026-10-13 09:57, orchestrator) - the adjudication rigs are resident, and mechanism A's acceptance line is now one number

Committed into `rounds/round40/orchestrator/`: `win_r91.py` (opcode-name-only window dump, positive-controlled at
`windows=0` on two Equal units), `merge_measure_r91m.py` (content-anchored multi-candidate merge onto a moving base
with the `merge_hunks.py` faithfulness proof, then install + regen + judge; self-tested to reproduce
`675ec7afa414bbb5` byte-exactly from landed + `[R21-63]`), and `fastgate_r91m.py`, which grades ANY candidate pair in
one command:

```
python -X utf8 fastgate_r91m.py --gen CANDIDATE_GEN --ana CANDIDATE_ANA --full
[installed] gen=... ana=...
[repro mechanism A]   <- the 12-line duplicated-while-test repro; 1/2 today, 2/2 means mechanism A is closed
[battery no-regression] RED=8/9  <- neighbouring if/elif chained-compare family, must not get worse
[broker] units=127/128 ... [_sync_worker windows] windows=9
[panel realtime|function|replace_utils|quote|quotation|order_api] 12/13 15/15 9/9 92/92 153/153 37/37
```

Landed baseline certified through it just now, including the trap that made the first version useless: the round-14
battery derives `ROOT` from its own `__file__`, so running the **repo** copy grades the repo's landed bytes no matter
which candidate is installed in the mirror - the battery had to be copied into the mirror at the same relative depth
(`ROOT=D:\Temp91m` in the output is the proof it is really grading the mirror).

Acceptance line for the round, so nothing has to be re-argued when candidates arrive: mechanism A is closed when the
repro reads **2/2**; the unit flips when broker reads **128/128** (GOLD already proves that text exists and is
judge-Equal); and any candidate that raises the battery above RED=8/9 or drops a panel row is rejected before a
190-second sweep is ever spent.
## Fifteenth addendum (2026-10-13 10:04, orchestrator) - mechanism A is ALREADY effectively closed: r93a's analyzer renders the GOLD shape for BOTH loops, one stray statement from Equal

I ran r93a's in-flight analyzer `1471c92eca157e46` (with the **landed** generator) through the fast gate, then dumped
the 12-line repro. Result:

```
[installed] gen=b4363f5858e58074 ana=1471c92eca157e46
[repro mechanism A] ***<module>.sync_worker: Failure: Different bytecode      <- was: Different control flow
                    [single] status=failure units=1/2
[battery no-regression] RED=8 / 9                                             <- neighbouring family untouched
[broker] units=127/128, sole failure _sync_worker   [_sync_worker windows] 9 -> 6
[panel] realtime 12/13  function 15/15  replace_utils 9/9  quote 92/92  quotation 153/153  order_api 37/37
```

and the repro product it emits is the GOLD text:

```python
    while True:
        while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading or int(datetime.datetime.now().strftime('%H%M')) >= post_after_trading or holiday_sync_account == '0' and not engine.data_proxy.is_trading_date(datetime.datetime.now().date()):
            time.sleep(60)
        while pre_before_trading <= int(datetime.datetime.now().strftime('%H%M')) < int(post_after_trading):
            time.sleep(1)
            pre_before_trading                <- the ONLY remaining defect
        time.sleep(2)
```

`orig instrs=170 prod instrs=172 delta=2`, **one** window: `+ @1106 POP_TOP`, `+ @1108 LOAD_FAST`.

What that means, and it changes the round's plan:
1. The judge's **CFG** comparison now PASSES on the repro (the verdict class changed from *Different control flow* to
   *Different bytecode*), so the duplicated-while-test folding - both loops, the 4-leg or-chain with the `and not`
   tail and the chained comparison - is correctly represented by r93a's rule. Mechanism A as I defined it (addendum
   11) is done; my earlier statement that mounting the chain "reaches none of the synthetic shapes" applies to
   r91a's candidate, not to this one.
2. The entire residual is **one discarded-value statement**: a leg's operand is loaded and popped as a bare
   expression statement after the loop body. That is the same stack-consumption distinction that gate 39's
   `[R21-56] _r2156_tail_is_bounded_statements` was built to decide (recover/emit only when the value is bound,
   returned, or passed; refuse when the consumer is `POP_TOP`) - the machinery exists, so this is a narrow conjunct,
   not a new axis.
3. Next hand's job, stated as one sentence: make the folded condition consume or drop the leftover leg operand so the
   repro reads `units=2/2`, then measure broker - `windows 9 -> 6` on the real unit with the same rule is the reason
   to expect a flip. Acceptance is already fixed: repro `2/2`, broker `128/128`, battery `RED<=8/9`, panel rows held,
   then the 402 CR-stripped sweep with `CHANGED = {trade_live_broker}` expected (predicate P fires on 1 of 173 loop
   conditions).
4. Caveat I will not paper over: `1471c92eca157e46` was read from a **live** engineer mirror, so it is a moving hash -
   a real measurement of the bytes I hashed, not a verdict on r93a's final deliverable. When its report lands I
   re-measure the delivered file before anything is installed.
## Sixteenth addendum (2026-10-13 10:16, orchestrator) - r93a DELIVERED and I corroborate it; my addendum 11 claim that "loop 2 is the same shape" is REFINED, not confirmed

r93a delivered analyzer `1471c92eca157e46` (pair) / `0f767ea7b09e93a9` (Half-1 only), generator untouched. Its own
measurements: loop 1 renders **byte-identical to GOLD**, the `del=61 @700..@1210` window is gone, predicate P census
with its real function = **402 files / 173 evaluations / 1 fire**, full 402-product CR-stripped sweep
**CHANGED = {trade_live_broker}**, six canaries at baseline, repro canary downgraded to `Different bytecode`, and
**broker stays 127/128 failing only `_sync_worker`**.

I measured the same bytes independently before its report arrived (my pinned snapshot at `rounds/round40/r93/`):
`_sync_worker windows 9 -> 6`, repro `Different bytecode 1/2`, panel 12/13 · 15/15 · 9/9 · 92/92 · 153/153, battery
`RED=8/9` unchanged. Agreement on every shared number.

The refinement of my addendum 11: I wrote that loop 2 is "the same duplicated-test shape", implying P covers it.
r93a measured otherwise and its numbers are specific - on loop 2 (`while pre_before_trading <= int(...) < int(post)`,
`@1890/@2072`) **P provably does not fire**: `forward-legs-outside = []` and `back_edge = 2844 != header = 2072`.
Reading the two together: loop 2's entry edge into its body start is an **unconditional** `JUMP_FORWARD @2064 -> @2072`
(my own edge census showed exactly two in-edges to `@2072`, that JUMP_FORWARD and `@2880 POP_JUMP_BACKWARD_IF_TRUE`),
because its condition is a single chained comparison rather than an or-chain. So the duplication law holds for both
loops, but P's *forward conditional leg* conjunct only exists for or-chain tests. Loop 2 needs a sibling predicate -
unconditional forward entry into the body start plus a conditional backward latch - which is the shape gate 36's
`_is_while_true` already recognizes for `while True`. Owner: r95a (R21-66). My "any A-side candidate that leaves
`@2832..@2884` as body statements is incomplete" warning stands; what was wrong is the implication that one rule for
or-chain loops automatically covers single-comparison loops.

Also measured by me and recorded honestly: two `merge_hunks.py` attempts to union r91a's `241905c2` with r93a's
`1471c92e` both FAILED the tool's faithfulness proof in **both orders** (3 residual blocks unexplained each way,
because each candidate's large insert lands inside the other's anchor context even though their landed-line footings
are disjoint). The merged artifacts hashed to `20b38ff7cfdb9232` in both directions and I fastgated one of them:
repro still `Different bytecode`, broker windows 6, panel intact - i.e. the unfaithful merge added nothing.
Conclusion: do not union r91a with r93a; r93a's rule supersedes r91a's for this unit, and if both are ever wanted the
transplant must be re-anchored by hand against the moved file, not spliced.
## Seventeenth addendum (2026-10-13 10:33, orchestrator) - per-window attribution baseline under `1471c92e`, for crediting whichever half closes what

I dumped `_sync_worker`'s windows under r93a's delivered analyzer with the landed generator (`orig 412 / prod 431`,
`delta=+19`, 6 windows). The point of this table is attribution: GOLD's own residual is **four small windows**
(`@542 +1`, `@696 -1`, `@700..@702 -2`, `@1210..@1212 -2`), and three of our six are already exactly GOLD's first
three - so loop 1 is at GOLD parity and everything left belongs to loop 2 and the reconnect tail.

| window | shape | whose job |
|---|---|---|
| #1 `@542 +1 ins` | matches GOLD #1 | already GOLD-parity (judge-patched / cosmetic) |
| #2 `@696 -1 del` | matches GOLD #2 | already GOLD-parity |
| #3 `@700..@702 -2 del` | matches GOLD #3 | already GOLD-parity |
| #4 `@1206..@1210 +24 ins` | GOLD has `-2 del` here | loop-1 exit / reconnect boundary - r96a (return-vs-break) is the candidate mechanism |
| #5 `@1382..@1214 -1/+163 replace` | GOLD has nothing here | the relocated second-loop body - r95a (loop-2 sibling predicate) |
| #6 `@1890..@2884 -165 del` | GOLD has nothing here | same defect seen from the original's side - r95a |

So the remaining distance is exactly two things: window #4 (24 instructions at the loop-1 exit, where GOLD deletes 2)
and windows #5+#6 (the whole second loop rendered in the wrong place because its duplicated test is not folded).
`delta` went from -2 (landed) to +19 because the fold emits the latch legs it now owns; that is not a regression in
itself - the judge still says `Different control flow` for the unit, and the pair's 402-product sweep is
`CHANGED = {trade_live_broker}`. When a half lands, the test is: does #5/#6 collapse (loop 2) and does #4 collapse
(reconnect/exit)? A candidate that shrinks only window count without moving these two groups is not a flip.
## Eighteenth addendum (2026-10-13 10:34, orchestrator) - DEFINITION OF DONE for `_sync_worker`: our folded product is 43 lines, GOLD is 45, and the whole gap is three textual facts

I diffed `out/broker_R93.py` (landed generator + r93a's `1471c92e`, generated in my mirror) against
`r91/broker_GOLD_PROOF.py` on the `_sync_worker` body. 25 diff lines, three facts, nothing else:

1. **Reconnect block: position and terminator.** GOLD places it right after loop 1 as four nested `if`s ending in
   `return`; ours places it later as one flat `if is_trading_date(..) and reconnect_flag is False and (…) and
   int(strftime) >= 900:` ending in `break`. This is r96a's item C, and the bytecode fact behind it is unchanged: the
   unit's only `RETURN_VALUE` is `@1874`.
2. **`sync_data_flag = 1` printed unguarded.** GOLD has `time_difference = abs((now - sync_account_time)...)` +
   `if time_difference > sync_max_time:` + the store under it (original `@2350/@2352/@2366/@2372/@2374`); ours prints
   the bare store (the `@2374` site) with its guard gone.
3. **Loop-2 latch still in the body.** Ours keeps `if not pre_before_trading <= int(strftime) < int(post): continue`
   plus a second, misplaced `time_difference = abs(...)` after `time.sleep(steps)`; in the original that comparison is
   loop 2's own duplicated re-test (`@2832..@2880`), not a body statement.

Facts 2 and 3 are one region (`LoopRegion@1890`, `hdr=2072 cond=1890 be=2844`, `is_chained_compare_cond True` per
r95a's dump) and belong to r95a/r98a; fact 1 belongs to r96a. When all three are gone the product *is* GOLD's text,
which I have already measured at `128/128`, so the flip criterion for the merged candidate is simply: this diff
reports zero hunks.
## Nineteenth addendum (2026-10-13 10:52, orchestrator) - the last hunk is a DECLARATION GAP: the reconnect chain owns no region at all

I ran r95a's read-only region dump (`rounds/round40/r95/dump_r95.py`, outside the analyzer so it cannot perturb the
product) over `@1200..@1950` on the pair bytes (`gen 0f4c3898` + `ana 1471c92e`, hashes re-verified in my mirror):

```
### @1210 n=1  owner=LoopRegion@232        JUMP_FORWARD 1214
### @1212 n=1  owner=LoopRegion@232        NOP
### @1214 n=16 owner=LoopRegion@232        succ=[1370, 1890]  preds=[544,702,1210,1212]   POP_JUMP_FORWARD_IF_FALSE 1890
### @1370 n=5  owner=LoopRegion@232        succ=[1388, 1890]  preds=[1214]                POP_JUMP_FORWARD_IF_FALSE 1890
### @1388 n=12 owner=LoopRegion@232        succ=[1502, 1524]  preds=[1370]
### @1502 n=5  owner=LoopRegion@232
### @1524 n=12 owner=LoopRegion@232
### @1638 n=15 owner=LoopRegion@232
### @1770 n=15 owner=LoopRegion@232
### @1872 n=2  owner=LoopRegion@232
### @1876 n=3  owner=LoopRegion@232
### @1890 n=17 owner=LoopRegion@1890        <- loop 2's own region starts here
```

Two facts, both new and both decisive for the last hunk:

1. **No region is declared for the reconnect chain.** All eleven blocks `@1214..@1876` carry `owner=LoopRegion@232`,
   i.e. they are unowned body blocks of the outer loop, while `@1890` begins a child `LoopRegion`. The generator
   emits that child region before the unowned blocks that precede it in the block order, which is exactly why our
   product prints the reconnect `if` **after** loop 2 while the bytecode places it before.
2. **The chain's shape is an `and`-guard sequence whose false legs all land on the next sibling's entry.** `@1214`
   (`is_trading_date(...)`) and `@1370` (`reconnect_flag is False`) both end in
   `POP_JUMP_FORWARD_IF_FALSE -> @1890`, and their true legs continue into `@1388 -> @1502 -> @1524 -> @1638 -> @1770`
   ending at `@1872/@1876` where the unit's only `RETURN_VALUE` (`@1874`) sits. So the chain has a common merge
   (`@1890`) and a terminal return leg - the data an identification-time rule needs, all of it region-own block data:
   entry block, the shared false-target across consecutive guard blocks, the true-leg succession, and the terminal
   opcode class of the last block.

Therefore the last hunk is **not** an emission-order tweak and **not** a `break`-vs-`return` patch at the emitter: it
is the missing declaration of an `IfRegion` (entry `@1214`, merge `@1890`, then-side ending in the `RETURN_VALUE`
block). Declaring it at identification time gives the generator a region to place *before* `LoopRegion@1890` and gives
the arm's terminator as its own block data, which is where the `return` comes from. That is the same principle as the
landed `[R21-55]` diamond-join recovery, and the failure mode to avoid is the post-hoc repair variant the campaign
already falsified on this file.

Checklist for whoever implements it (acceptance already fixed by measurement):
- declare the guard chain as one `IfRegion` with merge = the shared false target (`@1890` class: the entry of the next
  sibling region), keyed on consecutive blocks sharing a `POP_JUMP_*_IF_*` target plus a true-leg chain, with the
  then-side's last block terminating in `RETURN_VALUE`;
- the new region must be the sole owner of `@1214..@1876` (unique block membership; those blocks are currently claimed
  by the loop body, so the loop's own block list must shrink accordingly);
- after declaration, `dump` must show the blocks owned by the new region, `gold_diff` must go 2 → 0 hunks, and the
  judge must read `128/128`; `_process_order` and the six panel rows must hold, plus the 402 sweep with
  `CHANGED = {trade_live_broker}` (the pair is already certified collateral-free by me, so any new changed file is
  this rule's collateral).
## Twentieth addendum (2026-10-13 10:56, orchestrator) - the deferral site that puts the reconnect chain after loop 2

I traced how the loop-body emitter sequences statements (`region_ast_generator.py`):

- `_loop_generate_body` (`:8624`) keeps **two** lists: `body_stmts` and `back_edge_stmts`, plus
  `body_blocks_no_header`;
- `:8633 child_info = self._loop_collect_child_regions(region)`; `:8670+` a direct child `LoopRegion` is emitted as a
  whole as soon as a body block equals its `entry/header/condition` block or one of its `BoolOpRegion` chain blocks
  (`[Round 08 修复] _r08_nested_loop_child`) — which is how `LoopRegion@1890` gets emitted *while the outer body is
  still being walked*;
- blocks that "reach the back edge" are routed away from `body_stmts` into `back_edge_stmts`
  (`:9365 _loop_process_natural_back_edge`, `:14187/:14249 _loop_process_back_edge_with_condition`), and
  `_loop_postprocess` (`:8845` → `:14618`) then **appends `back_edge_stmts` at the END** of `body_stmts`
  (`:14723/:14725/:14727`), or folds them into an if-body at `:14718`.

So the reconnect chain `@1214..@1876` — which addendum 19 shows has **no declared region** (every block is
`owner=LoopRegion@232`) and whose guard legs all jump `POP_JUMP_FORWARD_IF_FALSE -> @1890`, the next sibling region's
entry — is being **deferred into `back_edge_stmts` and appended after the body**, which is precisely why the product
prints it after loop 2, and why its terminal `RETURN_VALUE @1874` arrives wearing a loop-exit (`break`).

Two legitimate remedies, and the difference matters for adjudication:
- **(A, declaration — r100a)**: identify `@1214..@1876` as an `IfRegion` (entry `@1214`, merge `@1890`, then-side
  ending in the return block). Then the generator has an abstract node to emit in block order and the arm's terminator
  comes from its own blocks. This is principle-3/4 clean and is my preference.
- **(B, role dispatch — r99a's risk area)**: refuse to defer a block into `back_edge_stmts` when its conditional-jump
  target is a sibling region's entry rather than the loop's own back-edge/header. Legal only if keyed on successor
  class (target is a region entry / not the header / not the back edge), and it is the over-fire-prone path — this is
  the same deferral machinery whose neighbours measured −269/−274 across 23 currently-Green files, so (B) demands the
  full 402 sweep before I even look at it.
A patch that instead *moves text* after emission (reordering `body_stmts` by offset in postprocess) is a post-hoc
repair and will be rejected regardless of what it measures, because the same class of repair was already falsified on
this file.
## Twenty-first addendum (2026-10-13 11:04, orchestrator) - integration costs measured: the two generator halves COLLIDE, the analyzer half composes

I rehearsed the three-way merge before any candidate was final, and it failed the tool's own faithfulness proof:

```
merge_hunks --base landed gen b4363f58 --candidate r99a live c46c6036 --current pair gen 0f4c3898
  FAIL: 6 residual block(s) not explained - merged 8164..8185 / 8190..8194 / 8200..8228 / 8239..8247 ...
```

Those footings are exactly r95a's territory (`_loop_generate_while`, 8126-8174 region), so r99a and r95a are editing
**overlapping code**, and a union cannot be spliced - it needs hand re-anchoring, which costs turns I do not have to
spare. Measured on the bytes as they stood: r99a's `c46c6036` over analyzer `1471c92e` still reads
**3 hunks from GOLD / windows=6 / broker 127/128** (panel and battery clean), i.e. so far it has not moved the unit.

Consequence for how I will close the round, in priority order:
1. **r100a's analyzer half is the integration-preferred route** - `region_analyzer.py` composes with the certified
   pair generator `0f4c3898` with no merge at all (different file), so if its declaration measures
   `gold_diff = 0 hunks` and `128/128`, I install `analyzer(1471c92e + r100a) + generator 0f4c3898` directly.
2. r99a's generator half is the fallback, and only usable by hand-porting its conjunct into the 8126-8247 region of
   `0f4c3898` - I will do that only if route 1 fails, and I will re-run the pair sweep afterwards because the merged
   file is then new bytes.
3. `clock_worker` (r101a) also lives in `region_analyzer.py` but on the **landed** analyzer; if it lands a flip it must
   be ported onto the `1471c92e`-based analyzer the same way, or installed alone. Two flips in one round are welcome;
   the gate consumes whichever union I certify, and a candidate that only reaches a partial stays banked.
