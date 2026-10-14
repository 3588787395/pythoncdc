# FIX_R21-57 — `<module>.TradeLiveBroker._sync_worker` on the gate-39 landed bytes

Ticket: **R21-57** (pre-assigned). Mirror `D:/Temp/r87`. Repo read-only, nothing installed.
**Verdict of this run: NO candidate delivered.** The unit needs at least three independent
mechanisms and its target source text is not yet pinned; all measurements are below.

## 0. Mirror certification + baseline re-measure (protocol 8)

```
core/cfg/region_ast_generator.py sha256[:16] = b4363f5858e58074   (gate-39 landed)  OK
core/cfg/region_analyzer.py       sha256[:16] = 842e2748bcdfeb66   (gate-39 landed)  OK
```
Regenerated `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
(179 288 B). It is **line-for-line identical to the committed `trade_live_brokerOK.py`**
(3062 lines, `identical`) → the mirror reproduces the landed bytes, so every number below is on
the landed base and not on a stale copy.

```
python -X utf8 scripts/pyc_verify.py single <pyc> --source out_base/trade_live_broker.py
[single] status=failure units=127/128 success_rate=99.22%
  ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
```

## 1. Premise re-measurement of the brief — CONFIRMED, with two corrections

`work/allwin_r63.py` on the landed bytes (`logs/allwin_base_sync.txt`), plus `unit_diff`:

```
len orig=404 prod=401 delta=-3
#1 replace orig[52..53 @362] prod[52..59]   del=1 ins=7
#2 insert  orig[70..70 @520] prod[76..113]  ins=37
#3 insert  orig[71..71 @522] prod[114..291] ins=177
#4 delete  orig[90..151 @700..@1210]        del=61
#5 delete  orig[235..397 @1890..@2884]      del=162
hunks=5 landings=6 judge_diff=True
```
Inserted = 7+37+177 = **221**, deleted = 1+61+162 = **224** → `delta=-3` is the net, exactly as
ADJUDICATION §9/§16 states. The five windows and the six landings are confirmed.

**Correction 1 (a claim in my dispatch brief is wrong on these bytes).** "`_sync_worker`'s loop
sits in the same try/except region" is **false for the failing loop**. `_sync_worker`'s
`co_exceptiontable` has exactly **3 entries, all inside the `with` block of the *second* loop**:
`2090..2168→2192`, `2192..2200→2200`, `2206..2208→2200`. The compound while at 232..1214 has
**zero exception edges**: 232's successors are `[364, 704]`, 364's `[522, 704]`, 522's
`[544, 702]`, 544's `[700, 1214]` — no handler member. The exception-edge blindness that
[R21-55]/[R21-56] were written to overcome does not exist on this unit's path.

**Correction 2.** Window #1 is not the same defect as #2..#5, and #4 and #5 are two *different*
defects (§5). Treating the unit as "one restructured loop body" understates it.

## 2. Does the landed [R21-55]/[R21-56] predicate reach this unit? — NO (measured)

`work/r2155_reach.py` instruments `RegionAnalyzer._r2155_diamond_join_from_value_blocks`
(rule at `region_analyzer.py:23384`, mount point `:25325`) and
`RegionASTGenerator._r2156_tail_is_bounded_statements` (`region_ast_generator.py:43236`), then runs
the whole region pipeline on the broker pyc (`logs/R2155_R2156_reach_broker.txt`):

```
JOIN calls=7  FIRES=6      all seven evaluated inside code object `_process_order`
                           (arm pairs 2642/2646, 2568/2572, 2390/2394, 2304/2308,
                            2230/2234, 1754/1758 -> joins 2648/2574/2396/2310/2236/1760);
                           one further call in `market_fund_transfer` (242/352) declines.
R2156 calls=2 TRUE=2 FALSE=0   (both on _process_order host-call spans)
JOIN code objects = ['_process_order', 'market_fund_transfer']
```
**Zero evaluations in `_sync_worker`.** Mechanically expected: the mount point is
`if merge_block is None` **inside the ternary-value-diamond candidate path**, entered only after
`_is_ternary_block` accepts both arms as single-value blocks. Every arm of the failing loop ends
in a statement-level conditional jump (`POP_JUMP_FORWARD_IF_*`), so predicate ③ ("`false_block`
must not end in a conditional/short-circuit jump") can never hold; and the one pair that looks
like a diamond (700 → 704, 702 → 1214) fails ⑤ because 704 has six predecessors
(232, 364, 700, 704, 876, 1056). Gate 39's new infrastructure therefore does **not** reach
`_sync_worker` — the brief's question has a negative, measured answer.

## 3. Why the while condition is not folded on the new bytes (cause re-measured, not re-run)

Region dump (`logs/region_tree_sync.txt`) — two LoopRegions share `entry=232`:

```
idx=2 LoopRegion entry=232 cond=None hdr=232 back=[2886] is_while_true=True   <- `while True:`
      children=[LoopRegion@232, LoopRegion@1890]
idx=1 LoopRegion entry=232 cond=232 hdr=704 back=[704]
      body=[704, 876, 1034, 1056, 1212]  else=[]
      blocks=[232,704,876,1034,1056,1212, 2064,2066,2168]      <- 3 foreign (loop2) blocks
      condition_chain_blocks=[232, 364, 522, 544, 1214, 1890, 2026]   <- legs + 3 foreign blocks
      children=[IfRegion@522, IfRegion@544, IfRegion@1034, IfRegion@1214,
                IfRegion@1388, IfRegion@1638, IfRegion@1770]
```
`work/condprobe.py` calls the **landed** detectors directly on that region
(`logs/while_chain_probe.txt`):

```
_detect_while_boolop_forward_chain(232, loop)        -> [(232,'or')]     # length 1 -> rejected
_detect_while_condition_nested_and_or_chain          -> None             # [R7-B45] is the mirrored shape
_detect_while_condition_boolop_chain (whole route)   -> [(232,'or')]
```
The single-leg result is produced at the **first** iteration: the walk's fall-through from 232 is
**364**, `block_to_region[364]` is the outer `while True` LoopRegion (idx=2), and
`LoopRegion.interrupts_boolop_forward_chain` is an unconditional `return True`
(`region_analyzer.py:666-668`). Hence no `BoolOpRegion` is ever created, `boolop_for_while` is None
in `_loop_generate_while`, and the generator renders `while A:` (leg 232 only) with the remaining
legs emitted as *body statements*: 876 → `return int(...) >= int(post_after_trading)`, 1034 →
`if holiday_sync_account == '0': continue`, 1056 → the bare `is_trading_date(...)` call. That is
product lines 843-847 and it is the origin of windows #1/#2/#4.

Same root cause ADJUDICATION §3 records for r71a, still present on gate-39 bytes (verified here
rather than assumed). I did **not** re-run the closed axis: no priority-table edit, no reclaim
guard, no back-edge fold, no `_r2144_*` variant. I also did not re-grade r79a's seven candidates
(the orchestrator's §16 table already does that on the landed generator); nothing I measured
contradicts it, and §2/§3 explain *why* none of them can flip this unit.

## 4. The unit's true source shape (`dis.get_instructions` + `co_lines()`; no hand-resolved jumps)

```
entry test  L1382 232..362  A = int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
                            @362 POP_JUMP_FORWARD_IF_TRUE  -> 704          (true leg -> body)
            L1383 364..520  B = int(...) >= int(post_after_trading)
                            @520 POP_JUMP_FORWARD_IF_TRUE  -> 704
            L1385 522..542  C = holiday_sync_account == '0'
                            @542 POP_JUMP_FORWARD_IF_FALSE -> 702 -> @1214 (false leg -> exit)
            L1384 544..698  D = self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
                            @698 POP_JUMP_FORWARD_IF_TRUE  -> 1214         (true -> exit  => operand is `not D`)
                            @700 JUMP_FORWARD -> 704    @702 JUMP_FORWARD -> 1214
body        L1386 704..742  time.sleep(60)
re-test     L1382 744..874  A' @874  POP_JUMP_BACKWARD_IF_TRUE  -> 704
            L1383 876..1032 B' @1032 POP_JUMP_BACKWARD_IF_TRUE  -> 704
            L1385 1034..1054 C' @1054 POP_JUMP_FORWARD_IF_FALSE -> 1212(NOP) -> 1214
            L1384 1056..1208 D' @1208 POP_JUMP_BACKWARD_IF_FALSE -> 704   @1210 JUMP_FORWARD -> 1214
exit        L1392 1214..    sequential code, still inside the same `while True:`
```
=> the statement is `while A or B or (C and not D): time.sleep(60)` — the brief's
"(A or B or (C and D))" with D negated — and the failing loop is **not** the `while True` (that is
the sibling region idx=2). Note the line inversion inside the last group (C on L1385 emitted
before D on L1384), which is the obstacle in §6.

## 5. Expressibility: what does a perfect loop1 render actually buy? (diagnostic, not candidates)

Hand-composed products (labelled `DIAGNOSTIC_*`; never a `*OK.py`), measured with the same rigs
(`logs/ideal_a_win.txt`, `logs/ideal_b_win.txt`, `logs/rp_win.txt`):

| shape | delta | windows | landings | judge |
|---|---|---|---|---|
| landed bytes (baseline) | −3 | 5 (−1/+7, +37, +177, −61, −162) | 6 | `Different control flow` |
| **A** §4 text substituted for the loop1 statement only | **+68** | 4 (−2, +23, +209, −162) | — | `Different control flow` |
| **B** §4 text **+** statement order loop1 → if@1214 → loop2 | **+19** | 4 (−2 @700/@702, −1 @1210, −19 @2214..@2372, +41 @2880ff) | 3 | `Different control flow` |
| runtime re-parent probe (children/break blocks restored; cross-region ⇒ unimplementable) | −3 | 5 | 6→3 | `Different control flow` (file still 127/128) |

So the compound-condition render **alone** leaves the whole second-loop placement defect
(−162/+209): the unit is not one mechanism. Render **and** order fixed still leaves two residuals:
(i) three unconditional `JUMP_FORWARD` stubs + a `NOP` that my source hypothesis does not
reproduce, and (ii) a *third*, independent defect inside loop2: `time_difference = abs(...)` and
`if time_difference > sync_max_time: sync_data_flag = 1` (orig 303..322) are emitted after the loop
instead of inside its body. Three mechanisms must close — the clock_worker pattern (task #57).

The runtime re-parent probe is recorded as a **falsified direction**: restoring the four sequential
IfRegions (1214/1388/1638/1770) to the outer loop and dropping the foreign break blocks
[2064, 2066, 2168] shrinks touched instructions 447 → ~126 and landings 6 → 3, and the judge still
reads `Different control flow`; moreover the rule needed to do it reads sibling-region ownership,
so it violates the own-data constraint regardless.

## 6. Open blocker: the exact source text of the last conjunct is NOT pinned

Variants compiled in `rigs/shape_probe.py`, `rigs/shape_probe2.py`, `rigs/shape_search.py`
(3.11.7, whole module, targets resolved by `dis`): `or C and not D` (flat), `or (C and not D)`
(parenthesised), `or (C and D is False)`, `or (not D and C)`, `(A or B) or (C and not D)`,
`A or (B or (C and not D))`, `or not (D or not C)`, `or not (D or C != '0')`, each both standalone
and inside the `while True:` context. **All reproduce the
entry/re-test duplication and the leg polarities, none reproduces
`@698 IF_TRUE->exit ; @700 JUMP_FORWARD->body ; @702 JUMP_FORWARD->exit` + `@1210 JUMP_FORWARD` +
`@1212 NOP`** — they thread the legs straight to the loop exit (0 `JUMP_FORWARD`). The line
attribution is the clue and the obstacle: C's instructions carry L1385 while D's carry L1384, so
evaluation order (C then D) is the reverse of that group's physical line order — a shape I could
not synthesise. Until the target text is pinned **no criterion can be validated against ground
truth**: my best hand-composed product is `delta=+19`, so today's ceiling for any identification
rule on this unit is provably not `128/128`.

## 7. Dispatchable follow-ups (one mechanism each, none a closed axis)

* **R21-57-a (diagnosis, no code)** Pin the 3.11 emission rule for the `(C and not D)` tail leg of
  an or-chain in a rotated while test: which source forms make CPython emit an exit stub
  (`JUMP_FORWARD -> exit` in its own block) instead of threading. Deliver the exact source text and
  a `compile()`-diff proof that the 404-instruction sequence is reachable. Everything else waits.
* **R21-57-b (generator, loop2 body order)** the −19/+41 residual: the chained-compare while
  re-test suppression at `region_ast_generator.py:8095-8180` removes the short-circuit exit blocks
  but the statements that follow the `with` block *inside the same body* come out after the loop.
  Own-data (the region's own `body_blocks` + back-edge block), no names/offsets; measurable alone.
* Do **not** re-dispatch: BoolOp reclaim guards, priority-table edits, `_r2144_*`, back-edge folds
  (§9/§16 closed; §3 shows the consumption site they need is still unreachable), and any
  cross-region re-parenting (falsified in §5).

## 9. Late additions (measured after §8 was written)

**9a. Third hand shape, `ideal_c`.** `rigs/mkideal3.py` = correct §4 compound-while text **and**
the duplicated leg statements (product lines 867-871) removed:
`delta=-71, hunks=5, landings=8, judge_diff=True`, file still `units=127/128` (`logs/judge_ideal_a.txt`,
`logs/judge_ideal_b.txt`). So all three hand shapes stay `Different control flow`; `ideal_b`
(delta +19) is the closest any text I can write gets, which is why §6 is the binding blocker.

**9b. The parenting / ownership leak that produces the −162/+177 inversion** (`logs/region_tree_sync.txt`):
the compound LoopRegion (idx=1, entry=232, cond=232, body=[704,876,1034,1056,1212]) has
`blocks=[232,704,876,1034,1056,1212, 2064,2066,2168]` — the last three blocks lie **inside the sibling
second loop** (entry 1890; 2064/2066 are its chained-compare short-circuit exits, 2168 is its
with-block exit) and are carried as that loop's `break_blocks=[2064,2066,2168]`. Because of them the
region's offset span reaches 2168, and the four sequential IfRegions that live **after** the compound
loop's exit (entries 1214, 1388, 1638, 1770) are attached as its `children` even though `1214 ∉
blocks`. Consequences measured: the outer `while True` emits the second loop before the `if`@1214
(product lines 848-866 then 872-876, original order is the reverse), which is exactly windows #2/#3
(inserts 37+177) paired with #4/#5 (deletes 61+162); `condition_chain_blocks=[232,364,522,544,1214,
1890,2026]` is polluted the same way (legs + 3 non-leg blocks). This is the axis the next ticket
should attack — it is neither a priority-table edit nor a reclaim guard, and it is visible from a
region's own `blocks` / `body_blocks` / child-entry data (a child entry outside the parent's own body
span, and a break block inside a sibling loop).

**9c. Why r71a's fold cannot be consumed even when built** (supports §3, does not re-run the axis):
the outer `while True` LoopRegion and the compound LoopRegion **share entry 232** (the original's
back edge `@2928 JUMP_BACKWARD -> 232` skips the `while True` NOP slot at @230, so both loops start
on the same block). `block_to_region` has one slot per block, so the legs 364/522/544 and the entry
232 can only be owned by one of them; every dump line `@364 -> LoopRegion@232` is ambiguous by name
and resolves to the outer loop. Any retention rule has to answer that two-deep loop sharing one
entry block is representable in the ownership table — that is the concrete open sub-question, and
no candidate I built depends on a guessed answer.

**9d. Nothing was installed and the repo was not written.** `git status --porcelain -- core/
site-packages` was not touched by this run (repo opened read-only; mirror-only edits), and
`build_cand_r87a_r2157.py` exits after certifying the landed bytes because `PATCHES` is empty.

**9e. Eight-variant shape search for the missing stubs** (`rigs/shape_search.py`): compiled
`A or B or (C and not D)`, the same without parentheses, `A or B or (not D and C)`,
`(C and D is False)`, `(A or B) or (C and not D)`, `A or (B or (C and not D))`,
`A or B or not (D or not C)`, `A or B or not (D or C != '0')` — each inside the real
`while True:` context (loop1 + the reconnect `if` + `time.sleep(steps)`). Every variant emits the
leg polarity sequence `PJ_IF_TRUE PJ_IF_TRUE PJ_IF_FALSE PJ_IF_TRUE …` but **0 `JUMP_FORWARD`
stubs**; the original emits 2 (`@700 -> body`, `@702 -> exit`) plus `@1210 JUMP_FORWARD` and
`@1212 NOP`. So the exit stubs are not a function of the or/and grouping I can reach by
re-parenthesising — they need either a different construct (e.g. the group's result materialised as
a value) or they come from the surrounding statement context, which is why §7-a exists.

**9f. No collateral inside the file.** All four non-landed products in `products/` (three hand ideals
+ the runtime probe) judge at `units=127/128` with the single FAIL line
`***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow` (`logs/judge_ideal_*.txt`,
`logs/judge_reparent.txt`): the other 127 units are insensitive to every loop1/loop2 rendering change
tested here, so a future flip of this unit really is a 128/128 file flip rather than a trade.

**9g. Two more re-measurements of the brief.** (i) The §6 stub question was searched over eight
groupings, not three — see `rigs/shape_search.py`; all eight emit **0** `JUMP_FORWARD` stubs where
the original emits 2 (+`@1210` and `@1212 NOP`), so the stubs are not reachable by re-parenthesising
the or/and group. (ii) The brief's "5 unfiltered windows, 6 landings" and every window bound are
confirmed verbatim (§1); the shape of window #1 is `replace` not `insert`, and its `del=1 ins=7` is
reproduced exactly.

**9h. New candidate direction worth one dispatch (measurement-backed, not a reclaim guard).**
The emission inversion behind windows #2/#3/#4/#5 correlates with two ownership violations visible
in one region's own data (`logs/region_tree_sync.txt`):

* the compound LoopRegion (idx=1, entry=cond=232, body=[704,876,1034,1056,1212]) carries
  `break_blocks=[2064,2066,2168]`; 2064/2066 are the *chained-compare short-circuit exits* of the
  next sibling loop (entry 1890) and 2168 is that loop's with-block exit, i.e. a loop is claiming
  break blocks that lie inside a sibling loop's body. They inflate its span to 2168;
* `block_to_region[1214] = LoopRegion@232` while `IfRegion@1214` (the reconnect statement, whose
  entry 1214 is the compound loop's own *exit* block and is **not** in the loop's `blocks`) is
  attached as that loop's child, along with IfRegion@1388/@1638/@1770.

A rule that refuses a break-block candidate whose successors/owner place it inside a sibling loop,
and consequently refuses the child attachment for a region whose entry the loop does not own, is
own-data (successor/predecessor + entry-identity only) and is testable without touching any
BoolOp priority or reclaim path. Predicted effect, from my runtime re-parent probe: touched
instructions 447 → ~126 and landings 6 → 3, **judge still `Different control flow`** — so it is a
co-requisite half, not a flip, and it must be dispatched as such (it cannot clear the 128/128 bar
alone).

**9i. Census for the §9h signature before anyone designs a rule** (`rigs/leak_census.py`, run on the
20-file panel, `logs/leak_census_panel.log`). Counting rule, stated with its numbers:
*LEAK* = one `(loop, break_block)` pair where `break_block ∈ loop.break_blocks` and that block is in
some **other** LoopRegion's `body_blocks` while not in this loop's own `body_blocks`;
*NARROW* = the LEAK pairs whose loop has `condition_block is not None` (i.e. a real while test, not a
`while True`); *SHARED* = one LoopRegion whose entry block is also the entry of another LoopRegion.

```
files=20   LEAK=18   SHARED=7   NARROW=6
  NARROW trade_info_utils.check_and_update_trade      loop_entry=10   cond=10   break=1136   <-- GREEN unit at base
  NARROW trade_live_broker._sync_worker               loop_entry=232  cond=232  break=2064 / 2066 / 2168  (3 pairs, ours)
  NARROW realtime_event_source.clock_worker          loop_entry=5598 cond=5598 break=6690   <-- the other failing unit
  NARROW risk_calculation._save_testds_to_csv        loop_entry=108  cond=108  break=246    <-- GREEN unit at base
```
So the signature is **not** unit-specific: 6 NARROW pairs over 20 files, 3 of them ours, **1 in
`clock_worker` (the only other residual unit in the corpus)** and 2 in units that are Equal at base.
Two consequences for the next dispatch, both measured rather than assumed: (i) a rule on this
signature has a real chance of moving two residual units at once, which is why it is worth one
dispatch; (ii) it necessarily *evaluates* on two green units, so the collateral protocol is not
optional — the 402-regen byte-diff and per-changed-file judge run are mandatory, and the rule must
be written so that a decline leaves the product byte-identical (the landed [R21-55]/[R21-56] style:
return `None`/`False` before any block or offset is registered). `SHARED=7` also warns that
entry-sharing between two LoopRegions is common (7 sites over 20 files), so §9c's sub-question is a
corpus-wide one, not an `_sync_worker` curiosity.

## 10. Protocol compliance

1. Collateral sweep: **not run** — I propose no install, so there is no candidate to sweep. Stated
   rather than faked; the 20-file panel could not have changed a no-candidate conclusion.
2. Ablation resets both core files: n/a (no halves measured). My mirror was certified from the repo
   in one copy operation and both sha16s are printed in §0 and by `build_cand_r87a_r2157.py`.
3. Census before editing: no edit performed. The censuses I did run are §2 (rule reachability over
   the broker pyc, with code-object names and arm offsets printed) and §3 (landed detector outputs).
   Membership counting rule used for §2, stated so a re-run reproduces it exactly: **one "call" =
   one entry into `_r2155_diamond_join_from_value_blocks` with a non-None arm pair; one "fire" = a
   non-None join block returned** → 7 calls / 6 fires, 0 calls in `_sync_worker`.
4. Correct-at-identification: nothing installed; §7-a/b are stated as structural / opcode-class rules.
5. Halves table: §5 carries `delta / windows / landings` **and** the judge verdict side by side.
6. This doc was written immediately after §0/§1 and appended as each measurement landed.
7. Every brief claim re-measured: five windows + six landings + `delta=-3` CONFIRMED; "+221
   inserted / −224 deleted" CONFIRMED; "the loop sits in the same try/except region" FALSIFIED
   (§1 correction 1); closed-axis list ACCEPTED (not re-run; §2/§3 explain the mechanism of it).
8. All commands < 300 s (slowest ≈ 25 s), `python -X utf8` only, no repo writes, no `*OK.py`
   hand-edits, all work inside `D:/Temp/r87`.
9. Protocol 1 substitute: since there is no candidate, I ran the mandated all-402 regen on the
   **landed bytes** instead, as a mirror-trust witness — see `logs/SWEEP_landed_run.log` and
   `logs/SWEEP_landed_cmp.log` (the sweep is the same rig r86a used; changed-file list is expected
   and reported as 0, which is what makes every number in this doc attributable to the landed bytes
   rather than to my mirror).
