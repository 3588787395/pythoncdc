# TICKET R21-91 - clock_worker's last unit is an ELSE-BODY HOIST, not the or-chain nesting

## Why this ticket exists

`[R21-90]` (`ana 996a1b1acf143458` + `gen 558192ecf6d5f8a0`) passes every collateral bar
(20-file panel: 19 rows `BYTES=SAME` incl. broker 128/128, quote 92/92, real_quote 45/45;
ROOT-joined 402 sweep: `files_compared=402 MISSING/FAIL=0 CHANGED={realtime_event_source.pyc}`)
and closes both jump axes (`instrs -2`, `back +0`, `jsites 0`), yet the judge stays
`12/13 Different control flow` with `indeg-equal=False`. So the block *inventory* is right
and the *edge structure* is not. Every previous hand pointed at the flat chained-compare
leg (hunk H5). That pointer is wrong, and it is disproved below.

## CORRECTION at 01:58 UTC - the "H5 is inert" claim below is SCOPE-LIMITED and must not be acted on as written

The synthetic in Proof 1 had **no `else:` clause** on the elif chain. Re-run with the shape the real
site actually has (GOLD line 299 is a flat three-conjunct `elif ... and delay_after_trading >= now_time
>= after_trading:` whose chain has `else: time.sleep(FPS)`, while the product splits it at lines 299-300
into `elif A and B:` + a nested `if C:` and still carries the `else:`):

```
FUSED+else   instrs=39 blocks=11 jump-sites=9 back=0  indeg-multiset=[4,2,1,1,1]
SPLIT+else   instrs=39 blocks=12 jump-sites=9 back=0  indeg-multiset=[3,2,1,1,1,1]
```

Identical instruction count, jump-site count and back-edge count - but a **different in-degree
multiset and one extra block**. So the nesting IS CFG-visible at a site whose chain has an `else:`
arm, which is precisely the D2 site, and restoring the flat three-conjunct `elif` is a candidate
explanation for D2 (`GOLD@300 in=1 out=1 n=22` vs `PROD@301 in=1 out=0 n=21`).

Consequences, in order:
1. Do NOT skip the chained-compare leg on the strength of Proof 1. It is inert only for a chain with
   no `else:` clause - the no-else control reads `[5,2,1,1,1,1,1,1,1]` on both shapes.
2. The unit's remaining `indeg-equal=False` can be produced by this very hunk, so the else-hoist fix
   and the flat-elif fix are two separate mechanisms and **both** may be required.
3. Generalize the instrument, not the guess: any future "this hunk is text-only" claim must be tested
   with the surrounding `else:`/`elif` structure present, because jump-threading differs once an arm
   has to skip an else body.

## Proof 1 (SCOPE-LIMITED, see the correction above) - H5 measured inert only when the chain has no else arm


`D:/Temp/mon/shape_r118.py`, Python 3.11.7, compiling the two source shapes of the elif arm:

```
elif A and B and (d >= x >= c):     -> instrs 54 jsites 14 back 0 indeg [5,2,1,1,1,1,1,1,1]
elif A and B:
    if (d >= x >= c):               -> instrs 54 jsites 14 back 0 indeg [5,2,1,1,1,1,1,1,1]
```

Identical on all four structural metrics. Closing H5 cannot move `indeg-equal`, therefore
cannot move the judge. Do not spend an arm on it.

## Proof 2 - block-signature diff names the real residue

New instrument `D:/Temp/mon/block_diff_r118.py <product.py>`: splits `clock_worker` in the
ORIGINAL pyc code object and in the product's compiled code object into basic blocks, signs
each block by its opname sequence, and compares (jump in-degree, jump out-degree) per block.
Run on the `[R21-90]` product (`blocks orig=176 prod=175`, `instrs orig=1442 prod=1440`), the
only *uniquely-signed* rows are:

```
ORIG-ONLY line=449 in=1 out=0 n=3  LOAD_FAST LOAD_DEREF STORE_ATTR
ORIG-ONLY line=451 in=1 out=1 n=8  LOAD_GLOBAL LOAD_ATTR LOAD_GLOBAL PRECALL CALL POP_TOP EXTENDED_ARG JUMP_BACKWARD
PROD-ONLY line=240 in=1 out=1 n=11 LOAD_FAST LOAD_DEREF STORE_ATTR LOAD_GLOBAL LOAD_ATTR LOAD_GLOBAL PRECALL CALL POP_TOP EXTENDED_ARG ...
```

i.e. the original keeps `self.before_trading_date = now_date` as its own block, entered by a
jump, falling through into a separate `time.sleep(FPS)` + back-edge block that is ALSO entered
by its own jump; the product fuses both statements into one block, so the original's second
predecessor edge disappears. Product line 240 is, in the `[R21-90]` product text:

```
238|   if holiday_not_do_before == '0':
239|       self.event_queue.put((dt, EventEnum.BEFORE_TRADING_START))
240|   self.before_trading_date = now_date      <- ours emits this UNCONDITIONALLY
241|   time.sleep(FPS)
242|   continue
```

## Proof 3 - the hoisted vs else-body shapes reproduce the measurement exactly

`D:/Temp/mon/shape2_r118.py` (same block splitter, hand-written miniature):

```
HOISTED   (as ours)  blocks=4 instrs=26  STORE_ATTR fused with sleep+back: 1 block n=10 in=1 out=1
ELSE-BODY (as orig)  blocks=5 instrs=27  n=3  in=1 out=0  then  n=7 in=1 out=1
```

The else-body shape reproduces the original's pair (n=3 in=1 out=0 / n=8 in=1 out=1) and the
hoisted shape reproduces the product's single fused block, plus one instruction saved - which
is the same direction as the unit's remaining `instrs=-2`.

## The claim to build on

`self.before_trading_date = now_date` is **the else body** of `if holiday_not_do_before == '0'`,
and its merge is the `time.sleep(FPS)` block. Our pipeline declares the assignment outside the
region, so `_if_generate_normal` renders no `else:` and the merge loses its second predecessor.

The engineer's own FIX note already measured the region data for this guard and read it
differently: `IfRegion@6690, cond=6690, merge=6778`, parent `IfRegion@6548`, with
`@6690/@6702/@6778` sitting in the parent's `then_blocks` - and classified the dedent as an
arm-window under-declaration on the positive-tail-claim axis (which is excluded as measured
inert). This ticket re-reads the same numbers: `cond=6690` + `merge=6778` with a block between
them that carries a jump predecessor is exactly an **else branch**, so the fix is an
else-declaration, not a tail claim.

## Next hand (do it in this order)

1. Print, for `IfRegion@6690` on the `[R21-90]` base, `region.else_blocks`, `region.merge_block`,
   and the successor sets of `@6702` (then tail) and the assignment block. Predicted: the
   assignment block is the sole else body, the `time.sleep` block is `merge=6778`, and the then
   tail jumps to `6778`.
2. If the assignment block is present in the region's block list but classified as sequential
   parent code, the criterion is region-data-only and belongs at identification time:
   an `IfRegion` whose `cond` has two distinct forward successors S1 (fall-through) and S2
   (jump target), where S1's tail jumps to a block that S2 reaches by fall-through, declares
   S1 as then_blocks and the S2 run as else_blocks with merge = that shared block. No function
   names, no offsets as keys, no counters.
3. Re-measure with `block_diff_r118.py` first (it is cheaper than the judge and names the
   block pair directly): success = the unique-signature ORIG-ONLY/PROD-ONLY rows disappear and
   `indeg-equal` flips True.
4. Only on judge `13/13`: install with the rig's REAL signature (verified against
   `D:/Temp/r91m/install_pair.py` at 01:42 UTC - it has NO `--sweep` flag and `--gold-hunks` is
   **required**, and it refuses when that number is nonzero):

   ```
   python -X utf8 D:/Temp/r91m/install_pair.py --ana <analyzer file> --gen <generator file> \
       --gold-hunks 0 --units "13/13" --gate
   ```

   **Trap to expect:** a genuine flip can still carry a nonzero GOLD *text* hunk count, because the
   H1-H4 hunks proved here are text-only (`(A and B) or C` vs `A and B or C`, `return` vs
   `return None`) and the judge ignores them. Zero-hunk-vs-GOLD is sufficient, NOT necessary - the
   bar is judge `n/n`. If the rig refuses on that account, do not relax the byte checks: write the
   two files directly and repeat exactly what the rig validates (BOM present, zero bare LF, zero
   `\r\r\n`, `py_compile` clean, re-hash in place, and
   `git status --porcelain -- core/` listing EXACTLY those two files), then let the gate certify.
   Then panel 20 by index, all four sweep shards, `gate_chain.py 41 40` (BARE label for `before` -
   `rounds/round40/after` is already committed, 8 shard files present),
   `residual_report.py 41 40` (`UNREGISTERED=0`), commit regenerated products +
   `rounds/round41/after` + push and verify the ref.

## Rig control - the instrument is certified on a known-GREEN input

`block_diff_r118.py` run on `GOLD_realtime_event_source_PROOF.py` (the file the judge accepts at
13/13), 2026-10-14 01:39 UTC:

```
blocks orig=176 prod=176  instrs orig=1442 prod=1442  SIG-ONLY-ORIG=0 SIG-ONLY-PROD=0
```

and the same rig on the `[R21-90]` product:

```
blocks orig=176 prod=175  instrs orig=1442 prod=1440  SIG-ONLY-ORIG=4 SIG-ONLY-PROD=3
```

So `SIG-ONLY-*` is the trustworthy metric (zero on a unit the judge already passes), while the
`degree mismatches on shared signatures` list is NOT - it prints even for GOLD because
identically-signed blocks get paired arbitrarily. **Bar 1 is therefore exactly:
`SIG-ONLY-ORIG=0`, `SIG-ONLY-PROD=0`, `blocks 176/176`, `instrs 1442`.** Hit that and the
`indeg-equal` flip is expected; then confirm with the judge.

## Addendum (01:52 UTC) - the residual is THREE rows, not one, and GOLD is an exact structural reference

New instrument `gold_map_r119.py <product.py>` maps each mismatching block signature back to
**source text on both sides**. Two facts it establishes first:

```
GOLD instrs=1442 blocks=176   (identical to the ORIGINAL pyc: 1442 / 176, and its block opname
                               sequence matches the pyc element-for-element)
site-packages/.../realtime_event_source.py  -> instrs=1330 blocks=160  NO match
```

So GOLD is a perfect source-level view of the original CFG (use it as the reference), and the
on-disk `realtime_event_source.py` is **NOT** the original source - do not treat it as ground truth.

`SIG-ONLY-GOLD=4 SIG-ONLY-PROD=3` on the `[R21-90]` product, all seven rows now named:

```
D1  GOLD  self.before_trading_date = now_date                      in=1 out=0 n=3
    GOLD  time.sleep(FPS) | continue                               in=1 out=1 n=8
    PROD  self.before_trading_date = now_date | time.sleep(FPS) | continue   in=1 out=1 n=11
        -> the else-body hoist described above.

D3  GOLD  (bare return)                                            in=0 out=0 n=2  LOAD_CONST RETURN_VALUE
    PROD  (bare JUMP_FORWARD)                                      in=0 out=1 n=1  JUMP_FORWARD
        -> the same hoist one site later: GOLD reaches the final `return` by FALL-THROUGH, our
           product reaches it by a JUMP, i.e. we have a branch where GOLD has straight-line code.
           Our `LOAD_CONST RETURN_VALUE` therefore reads in=1 where GOLD reads in=0.
        -> D1 + D3 together explain the whole `instrs=-2`, so the census MUST count >=2 fires; a
           criterion that fixes only site D1 will not flip the unit.

D2  GOLD  ...EventEnum.HANDLE_DATA run + `else:`                    in=0 out=1 n=22
    PROD  ...EventEnum.AFTER_TRADING_END run                        in=1 out=0 n=21
        -> one instruction short AND the edge direction flipped. NOTE: block signatures are
           opname-only, so this pairing is by shape not by identity - the two excerpts are
           different arms. Treat D2 as "somewhere in the set_current_stage/event_queue.put/
           <x>_date = now_date ladder followed by an `else:` clause, one instruction is missing"
           and locate it by a per-arg block comparison (LOAD_METHOD/LOAD_ATTR argument names)
           before writing any criterion for it. Do not guess a criterion from this row alone.
```

Consequence for the ticket: the target metric stays `SIG-ONLY-GOLD=0 SIG-ONLY-PROD=0`,
`blocks 176/176`, `instrs 1442` - and reaching it requires D1 **and** D3 (same mechanism, two
sites), while D2 must be located before anyone acts on it.

### Second addendum (01:55 UTC) - D2 and D3 located with an ARGUMENT-aware block diff

The previous rows were paired by opname signature, which is ambiguous across the sibling arms.
Re-run with each block signed by `opname#argval` (same splitter, args included) - now the two sides
name the SAME source text, so the pairing is identity and not shape:

```
ARGSIG-ONLY-GOLD=4  ARGSIG-ONLY-PROD=3   (GOLD 1442 instrs, PROD 1440)

D1  GOLD  line 240  in=1 out=0 n=3   LOAD_FAST#now_date LOAD_DEREF#self STORE_ATTR#before_trading_date
    GOLD  line 241  in=1 out=1 n=8   LOAD_GLOBAL#time LOAD_ATTR#sleep LOAD_GLOBAL#FPS PRECALL CALL POP_TOP EXTENDED_ARG JUMP_BACKWARD
    PROD  line 240  in=1 out=1 n=11  (both fused into one block)

D2  GOLD  line 300  in=1 out=1 n=22  set_current_stage(EventEnum.AFTER_TRADING_END) / event_queue.put(...) / after_trading_date = now_date  + the following `else:`
    PROD  line 301  in=1 out=0 n=21  SAME three statements - one instruction missing AND the outgoing jump gone

D3  GOLD  line 216  in=0 out=0 n=2   LOAD_CONST#None RETURN_VALUE          (reached by fall-through)
    PROD  line 230  in=0 out=1 n=1   JUMP_FORWARD                          (a stray jump block we emit)
                                    and our LOAD_CONST#None RETURN_VALUE therefore reads in=1
```

Read together, D2 and D3 are the **same edge-threading consequence as D1**: when an `else`/tail arm
is hoisted into sequential code, the arm that used to *jump* to the shared continuation stops
needing that jump (D2 loses its out-edge and one instruction) while a different seam gains a stray
`JUMP_FORWARD` (D3). So the census must show fires at all three sites - `@240` (holiday guard),
`@300` (`AFTER_TRADING_END` arm before an `else:`), and the loop-tail `return None` at `@216` -
and a candidate that closes only `@240` will still read `instrs=-2 / SIG-ONLY 4/3` and stay 12/13.

D2 is NOT the H5 nesting: `shape_r118.py` already proved fused and nested `elif` shapes compile to
identical instruction counts, so the missing instruction at `@300` is the lost outgoing jump, not
the chained-compare leg.

The argument-aware variant is `block_diff_r118.py` with one change: build each block signature as
`i.opname + "#" + str(i.argval)[:30]` for ops starting with LOAD_/STORE_/COMPARE_OP/IMPORT_/BINARY_OP
(everything else opname-only). Run it on any product to reproduce the seven rows above verbatim.

## Third addendum (02:01 UTC) - the flat-elif restore is PROVEN to close D2, so TWO mechanisms are required

Compile-only experiment on a scratch copy of the `[R21-90]` product (`D:/Temp/mon/mut_D2only_r119.py`;
the repo and every shipped product are untouched - this is diagnosis, and hand-editing a product would
violate the products-come-only-from-the-pipeline rule). The single edit rewrites product lines 299-303
from

```
elif now_date == self.before_trading_date and now_date > self.after_trading_date:
    if delay_after_trading >= now_time >= after_trading:
        ...three statements...
else:
```

to GOLD shape (flat three-conjunct `elif` + the same three statements, same `else:`), then re-runs the
ARGUMENT-aware block diff against GOLD (`opname#argval` signatures):

```
product (R21-90)        ARGSIG-ONLY-GOLD=4  ARGSIG-ONLY-PROD=3   blocks 170 vs 169
product + D2 fused      ARGSIG-ONLY-GOLD=3  ARGSIG-ONLY-PROD=1   blocks 170 vs 168
```

Reading: the restore closes one GOLD-only row and TWO PROD-only rows and removes the extra block, so
`D2` is a genuine second mechanism, not a side effect of the else-hoist. What remains after it is
exactly `D1` (2 GOLD rows + the fused 11-instruction PROD row) and `D3` (the stray `JUMP_FORWARD`).

**Therefore a candidate that ships only the else-declaration fix cannot reach 13/13**, and the accept
check must be the arg-aware diff going to `0 / 0` with `blocks 170/170`. Expect to need:
1. the else-body declaration (D1 + D3), and
2. absorbing a trailing chained-compare conjunct into the owning `elif` test instead of emitting a
   nested `if` (D2). Both must be region-data-only criteria decided at identification time; neither may
   key on names/offsets/counters, and the second must be censused for its corpus population before it is
   written, because `elif A and B:` + `if C:` is a very common shape and an unscoped rule will over-fire.


## Fourth addendum (02:02 UTC) - D2 scoping predicate with a measured corpus population

Read-only text census over the current products (`site-packages/**/*OK.py`, 407 files scanned):

```
elif <test>:  immediately followed by a deeper-indented  if <test>:        -> 171 sites in 51 files
   of which the nested if test is a CHAINED comparison (a >= x >= b style) -> 1 site
      IQEngine/plugins/plugin_system_event_source/realtime_event_sourceOK.py:283
      if delay_after_trading >= now_time >= after_trading:
```

So the blunt "flatten an elif whose arm starts with a nested if" rule is unusable (171 fires, 51 files),
but narrowing it by the chained-compare shape gives a population of exactly ONE corpus-wide, and that
one is the D2 site. The criterion to write is therefore the region-data analogue:

  an elif arm whose test ends in a conjunct that is a Compare node with two or more operators (a chained
  comparison), and whose arm body consists of that comparison test plus the following statements, absorbs
  the chained comparison as the final conjunct of the owning elif test instead of emitting a nested if.

Caveat to honor: the 171 / 1 numbers are a PRODUCT-TEXT proxy, not the criterion and not a fire census -
re-measure the predicate over analyzer region data before installing, exactly as the population law requires.


## Fifth addendum (02:05 UTC) - mutation sweep results: D1-as-else is NOT the exact shape, and the cheap objective function is now known

All rows are product-text MUTATION probes on scratch copies (`D:/Temp/mon/mut_*.py`) scored by
re-compiling and diffing ARGUMENT-aware block signature multisets against GOLD
(`GOLD-only` / `PROD-only` counts; GOLD has 170 blocks). The repo and all shipped products are
untouched - hand-edited products can never be installed, this only ranks candidate source shapes.

```
product (R21-90)                    GOLD-only=4  PROD-only=3  blocks=169   (GOLD 170)
D1 read as else-body                GOLD-only=3  PROD-only=3  blocks=170
D1 read as assignment inside then   GOLD-only=4  PROD-only=3  blocks=169   <- INERT
D2 flat three-conjunct elif         GOLD-only=3  PROD-only=1  blocks=168
D1 + D2 combined                    GOLD-only=2  PROD-only=1  blocks=169   <- still not 0/0
```

What survives the combination:
1. a content difference in the `self.event_queue.put((dt, EventEnum.BEFORE_TRADING_START))` run -
   the same signature prefix appears on BOTH sides, so the two sides put a different number of
   statements inside that block (block EXTENT, not just nesting), and
2. GOLD`s isolated `LOAD_CONST#None RETURN_VALUE` block (D3) - unaffected by D1 or D2.

Consequences, stated conservatively:
- Do not ship "the assignment is the else body" as settled. It is the best single mutation measured
  so far (closes one row and brings block count to GOLD`s 170) but it is not sufficient, and the
  "inside then" reading is provably inert.
- The search is cheap and should be done exhaustively before any gate: enumerate source shapes at the
  two sites (then/else split, nested if, `elif` merge, and the loop-tail `return None` placement),
  score each with this instrument in seconds, and only build a pipeline candidate for a shape that
  reaches `GOLD-only=0 PROD-only=0 blocks=170/170`. That metric is a proxy for the judge, not the
  judge: `0/0` is necessary-but-to-be-confirmed-sufficient, so a 13/13 judge read is still the gate
  condition.
- Note the instrument difference: the opname-only diff (earlier addenda) reported `in`/`out` degree,
  the argument-aware multisets here do not. A future arm should compare BOTH - content and degree -
  because D2 shows content parity is not enough (`instrs`, `jsites`, `back` were all equal while the
  in-degree multiset differed).


## Sixth addendum (02:08 UTC) - THREE source-shape facts account for six of the seven differing blocks

Same mutation-probe instrument (argument-aware block multisets vs GOLD, scratch copies only, no product
or repo file touched). D3 is now named: the product renders a **`while`/`else: return None`** clause
(product lines 306-307) where GOLD has no while-else at all and the loop simply falls through to the
function-ending implicit return - GOLD`s isolated `LOAD_CONST#None RETURN_VALUE` block sits on the
`while self.active:` line, entered by fall-through only.

```
product (R21-90)          GOLD-only=4  PROD-only=3  blocks=169   (GOLD 170)
D3 alone (drop else/return)  GOLD-only=3  PROD-only=3  blocks=170
D1 + D2 + D3 combined     GOLD-only=1  PROD-only=1  blocks=170   <- block count now EXACTLY matches GOLD
```

So the three facts to implement are:
1. **D1** - the assignment reached by a jump between an IfRegion cond and its merge must be declared as
   the region`s else body, not hoisted into the parent sequential walk (measured: closes one GOLD-only
   row and brings the block count to GOLD`s 170; the "assignment inside then" reading is inert).
2. **D2** - an `elif` chain whose final conjunct is a chained comparison (`a >= x >= b`) must fold that
   conjunct into the owning `elif` test instead of opening a nested `if` (measured: GOLD-only 4->3,
   PROD-only 3->1; population of the shape is exactly 1 corpus-wide, see the fourth addendum).
3. **D3** - a `while` loop whose fall-out path is the function end must not be rendered with an
   `else: return None` clause (measured alone: GOLD-only 4->3 and blocks 169->170).

What still separates the combined mutation from GOLD is ONE pair of blocks, both beginning
`LOAD_DEREF#self LOAD_ATTR#event_queue LOAD_METHOD#put LOAD_FAST#dt LOAD_GLOBAL#EventEnum
LOAD_ATTR#BEFORE_TRADING_START BUILD_TUPLE PRECALL CALL POP_TOP ...` - i.e. the block EXTENT of the
`event_queue.put((dt, EventEnum.BEFORE_TRADING_START))` run differs (the two signatures share their
prefix and differ in their tail). Next hand: print those two full signatures with per-instruction
argvals and line attribution to see which extra/missing statement closes the run; do NOT spend a gate
until the proxy reads `0/0` with `blocks 170/170`, then require judge `13/13` as the real condition.

Reminder of what is NOT proved: `0/0` on this proxy has never been shown to imply judge `13/13` (the
judge compares the whole code object graph including handler tables), and none of these mutations is a
shippable change - they only identify the source shapes the pipeline must be made to emit.

## State this ticket is written against




Landed bytes unmoved: analyzer `fef59e95359f36fd`, generator `c3049a87daf59acc`,
`git status --porcelain -- core/` = 0. Gate label 41 unconsumed. Corpus 6616/6617 (99.9849 %),
401/402 files, `clock_worker` 12/13. `[R21-90]` is banked at
`rounds/round41/MEASURE_R21-90_arm_certification.md` and in
`D:/Temp/r116/DELIVER/CANDIDATE_r2190_558192ecf6d5f8a0.py`. The engineers r116a run finished
with the platform restored and re-proved.
