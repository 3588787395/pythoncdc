# ADJUDICATION_ROUND39 — five engineers, four banked candidates, zero flips (2026-10-12)

Round 39 has consumed no gate label: the corpus still reads the gate-38 sealed
**6614/6617 (99.9547%), 400/402 files, residual 2 files / 3 units**
(`rounds/round38/RESIDUAL_ROUND38.md`, `UNREGISTERED=0`). Nothing from this round is installed;
`git status --porcelain -- core/ site-packages/` = 0 lines all round, and the landed bytes are still
generator `11324f276cce6d5b` / analyzer `f7d849e974904492`.

**Every number below was re-measured by me in a clean mirror (`D:/Temp/v39`, built from repo `core/
scripts/ parsers/ utils/ bytecode/ pycdc.py`), not copied from an engineer's report.** Where a
claim comes only from an engineer I say so.

## 1. Residual shapes on the landed bytes (measured 12:34, repo `unit_diff.py`)

| unit | shape |
|---|---|
| `realtime_event_source.clock_worker` | `orig=1424 prod=1311 delta=-113` (hunk 1 = the 17-instruction `if holiday_not_do_before == '0': event_queue.put(...)` body at `@6690`) |
| `trade_live_broker._process_order` | `orig=507 prod=439 delta=-68` (hunk 1 = 15 instructions `@1638..@1710`, the whole `strategy_log.info(_('生成订单…'))` statement) |
| `trade_live_broker._sync_worker` | `orig=404 prod=401 delta=-3` (hunk 1 = `POP_JUMP_FORWARD_IF_TRUE` vs our `IF_FALSE` + inline `time.sleep(60)`) |

## 2. Ticket numbering collision, fixed on the record

`R21-44` was taken twice today (r71a for broker `_sync_worker` compound-while, r73a for clock_worker
or-tail). From here I pre-assign numbers in the dispatch: **R21-45 = r74a**, **R21-46 = r75a**,
**R21-47 = r76a**. `rounds/round39/r71/FIX_R21-44_sync_worker_compound_while.md` and
`rounds/round39/r73/FIX_R21-44_clock_worker_or_tail.md` both keep their original filenames; the
collision itself is the finding, not a typo to hide.

## 3. `_sync_worker` — r71a, banked, `changed files = 0 of 20`

Analyzer candidate `0d568cdd7fe0f167` (`_r2144_detect_while_condition_nested_or_and`, the mirror of
the landed `[R7-B45]`, returning `or_run + and_group = [(232,'or'),(364,'or'),(522,'and'),(544,'and')]`).
Census `head_ok=1, FIRES=1` over the 20 panel files ⇒ corpus-unique. Judge stays **126/128**, delta
stays **−3** (no shrink). Cause of inertness, from the engineer's probe: the BoolOpRegion is built but
`analyze()`'s `block_to_region.clear()` + priority rebuild (`region_analyzer.py:1871` / `:4119`)
reclaims blocks 232/364/522/544 to the enclosing `while True` LoopRegion (BoolOp priority 20 loses),
so the generator never consumes it. Forced retention (the engineer's second product) proves the
generator rebuilds the compound test correctly but the backward recheck leaks `while False: pass`
and the delta **worsens −3 → +19**. Co-requisites to reopen: guard the condition-context BoolOpRegion
from the reclaim, and fold the re-test blocks as the loop back edge. I did not independently re-run
the reclaim probe (it is an in-process census, not a product reading); the product numbers I did verify
as unchanged from landed.

## 4. clock_worker — the real chain, and where it now stands

| base / candidate | sha16 | my measurement | judge |
|---|---|---|---|
| repo landed bytes | `11324f276cce6d5b` | `delta=-113 hunks=7` | 12/13 |
| P1+P2 re-anchored on gate 38 (r73a) | `cf5868e68208adf6` | `delta=-6`, hunks `@6778..@6782`(del 3) `@7270..@7308`(del 6) `@9210..@9212`(rep 2→3) | 12/13 |
| r73a or-tail [R21-44] on plain landed (half-alone) | `248d5253c432eb6b` | not installed; census 847 evals / 2 fires | 12/13 |
| r74a [R21-45] **A+B** on the anchored base | `f51f9de14d216cda` | **`delta=-4`**, unfiltered windows = spurious `JUMP_FORWARD` @6496, spurious `JUMP_FORWARD` @7254, and the 6-instruction `debug` loss @7270..@7308 | 12/13, broker 126/128, quote 92/92, quotation 153/153, order_api 37/37 |
| r74a A+B+R21-44 | `3e7af79a63b5d0cf` | `delta=-5` (closes a hunk, worsens the count) | 12/13 |
| r75a [R21-46] onlyA on r74c | `05abc061c9fb10ed` | `delta=+2`: `delete orig[1050..1067 @7268..@7368] del=17` **paired with** `insert @9194 ins=17` — the 17-instruction block is restored but emitted at the function tail | 12/13 |
| r75a A+B on r74c | `0a2f4a81c593b1c6` | `delta=+3`; **all three windows are single spurious `JUMP_FORWARD`** (@6496/@7254/@7592) | 12/13 |
| **best known** r75a A+B on r74d (A+B+R21-44) | `30a4d7827122e165` | **`delta=+2 / 2 windows / 7 landings`** | 12/13, no other file changed |
| r76a [R21-47A] gated relaxation of conjunct ⑧ | `e38c0348a48a35e6` | `delta=-274 / 5 windows` — window-for-window identical to the blanket relaxation r74a measured; blast radius 1 file | 12/13 |

Two corrections to my own dispatch briefs, both from r76a's re-measurement and confirmed by me:
1. My "r75's A restores content but misplaces it, so A+B must be the fix" framing was half wrong:
   **r75's A+B already emits the 17-instruction block inside its arm**; only A alone relocates it. The
   residual on that base is three single spurious forward jumps, not a loss.
2. The deliverable base is **not** r74c: `@6496` is a [R21-44] site, so best-known is `r74d + R2146AB`
   (`30a4d782`), which is why the residual is "+2 / 2 windows / 7 landings" rather than "+3 / 3".

## 5. The clock_worker blocker, stated as one named region to declare

`compile()` on 3.11.7 in jump-index topology (`rounds/round39/r76/SHAPE_topology_site7164.txt`) settles
the source shape at site `@7164`: `if A and B or C:` **then** `if D: debug(); if E: … ; <@7492 tail
sequential>`. The original matches all six in-window jumps; our product mis-threads three, and "flat
fold but keep @7492 as E's else" still mis-threads D's false exit (+49 vs the original's +36) — so the
fold and the else-tail are two independent requirements, not one.

Why nothing fires usefully: after the fold, the arm's `then=[@7248,@7270,@7492,@7372,@7488]` contains
`@7248`, which is owned by **no region** (only an `inline_boolop_chains` member with `op=None`), and
`_generate_block_statements` swallows it — which is exactly the −274 catastrophe. The named fix, per
r76a and endorsed by me as the correct next ticket: **declare a synthetic
`IfRegion(entry=@7248, then=[@7270], else=[], merge=@7492)`** (analyzer-side, at identification time)
paired with the phantom-else rule, as a co-requisite pair. This is the axis ticket R21-34 named three
rounds ago ("the outer if has no declared region so no block-level call can build its then arm").

Falsified on this unit, do not re-run: blanket or gated relaxation of [R21-44] conjunct ⑧ (−274);
the `_orphaned_blocks` release path as the emitter (0 events in this file); the `merge_block is None`
analyzer census (this code object has zero such IfRegions); treating `@7248+@7270` as one `B and C`
BoolOp (the `debug()` result is `POP_TOP`-discarded, i.e. a statement — the ibc fold is inexpressible).

## 6. What the round changed in method, not just in bytes

- **Nesting is a landing channel.** The campaign's standing conclusion "the generator has no landing
  channel" (three tickets) was too narrow: `R21-43` landed today (gate 38) precisely by re-nesting an
  elif chain, and every candidate in this file works the same lever.
- **Half-alone measurement is cheap and keeps lying impossible.** The pair installed at gate 38 needed
  both halves (generator alone = 27 differing bytes and still `Different`), and r74/r75's 2×2 tables are
  the only reason I could rank `30a4d782` without re-running four builds.
- **Two engineers died with usable bytes and no doc** (r75a truncated report, r71a's numbering
  collision). Reclaiming them cost me four independent judge runs plus four `unit_diff` runs; the
  successor briefs therefore demand "write the doc EARLY, append as you go".

Next gate label **39** still runs against `rounds/round38/after`; round 39 has not consumed it because
nothing landed.


## 7. r77a (R21-48) — killed by the subagent turn cap, but its two premise corrections are the round's best finding

Delivered `rounds/round39/r77/` (6 candidates + a doc whose §4–§6 are placeholders) and left the mirror at the
base bytes. I ran its 2×2 myself in `D:/Temp/v39`, judging and diffing each product:

| variant | my `unit_diff` | my judge |
|---|---|---|
| base `30a4d7827122e165` | `delta=+2` (2 windows, 7 landings) | 12/13 |
| A (elif-chain-filter guard) | `delta=+3` | 12/13 |
| B (phantom-else rule) | `delta=+2` | 12/13 |
| A+B | `delta=+3` | 12/13 |

So the co-requisite pair it predicted (2 spurious jumps disappear → 13/13) is **falsified**: A costs a jump,
B is neutral, and the pair is `delta=+3`. Banked, not installed.

Two corrections it made to my own dispatch brief, both with probe output, and I endorse them because they
are read from code rather than inferred:
1. **There is no "ordering wall" in the conditional-region walk.** `region_analyzer.py:18826` sorts
   `blocks_in_reverse` with `reverse=True`, i.e. **descending** offsets, so children (larger offsets, e.g.
   `@7270`) precede parents (`@7248`) — which is the correct bottom-up reduction order. My brief asserted the
   opposite (ascending, parents first) and told it to work "with" a wall that does not exist. Project memory
   carries that claim from ticket R20-4, so it needs re-derivation before any future brief cites it.
2. **`IfRegion@7248` is not never-built — it is built and then removed.** Probe:
   `BUILD_BASIC_IF for @7248: then=[7270,7372,7488] else=[] merge=7492 → IF_THEN entry=7248`, after which the
   elif-chain filter (`region_analyzer.py:1672-1691`) deletes it because `@7248 ∈ IF_ELIF_CHAIN@7186.elif_conditions`.
   `block_to_region[@7248]` finally belongs to the enclosing `TryExceptRegion` (priority 70 > IF_THEN 25).
   `IF_ELIF_CHAIN@7186.elif_bodies=[[@7372,@7488]]` omits `@7270`, `@7248`'s real true successor — i.e. `@7248`
   is not an elif of that chain but the nested `if D` inside the `@7216` arm. That reframes the residual from
   "declare a synthetic region" to "**the chain mis-collected an elif condition**", which is the same family as
   the landed `[R21-B4]` refusal in `_build_elif_region` — the next ticket should attack the collection, not
   the filter.

Clock_worker has now had six tickets today: r73a, r74a, r75a, r76a, r77a, plus the re-anchor. Best banked
state remains `30a4d7827122e165` at `delta=+2 / 2 windows / 7 landings`, judge 12/13, `changed files = 1`.


## 8. r78a (R21-49) — the elif-mis-collection reframe is FALSIFIED too, with clean numbers

I framed the residual as a collection defect (the chain claims `@7248` as an elif condition while
`elif_bodies=[[7372,7488]]` omits `@7248`'s true successor `@7270`). r78a re-measured the premise and it
**holds** — inert probe, `true_in_body=False`, the sibling `@6846/@6868` correctly does not fire (it is a
pre-formed BoolOpRegion pure operand), census 230 evaluations / **1 fire**, membership
`two_owner=186 / zero_owner=0` identical base-vs-candidate — but both fix granularities destroy the unit:

| variant | delta | windows | landings | judge |
|---|---|---|---|---|
| base `30a4d7827122e165` | `+2` | 2 | 7 | 12/13 Different control flow |
| A: walk `break`, don't fold `@7270` | `-269` | 4 | 2 | 12/13 |
| B: `return None`, refuse the `@7186` fold | `-269` | 4 | 2 | 12/13 |
| A+B | = B (A subsumed; byte-identical product) | | | |

Cause, from its own reading: `@7186` is a single-elif chain whose `elif_final_else` is **44 blocks = the
entire function tail**, so derefusing `@7248` makes a downstream merge guard abandon the fold and orphan the
tail. `changed files = 1`, and it is the target, **regressing** `+2 -> -269`. Banked, not installed.

**Axes closed on clock_worker in one day (eight engineer-runs):** filter-suppression + phantom-else pair
(R21-48), conjunct-8 relaxation blanket and gated (R21-44/47, twice), `_orphaned_blocks` as the emitter,
`merge_block is None` census, the `@7248+@7270` BoolOp reading, and the elif mis-collection (R21-49). What is
LEFT is not a collection or placement problem: **two spurious `JUMP_FORWARD`s at `@7252` and `@7590`** (arm
tails of `@7164`/`@7186`) plus 7 landing diffs. r78a concludes "the generator has no landing channel", but
that sentence was already proven too narrow today by the landed `[R21-43]`; the honest statement is that
*neither a declaration nor a collection rule reaches these two jumps — what is untried is the arm-tail
emission shape itself (which arm falls through vs. takes the explicit jump), i.e. the `[R21-36]`
continue-arm-hoisting family, on the analyzer side of the region data.*

Best banked base for the next hand stays **`30a4d7827122e165`** (`+2 / 2 windows / 7 landings`), and the
corpus stays at gate 38's **6614/6617, 400/402 files** because nothing from this round was installed.


## 9. r79a (R21-50) — the `_sync_worker` reclaim-guard + back-edge-fold pair, measured by me after its run was cut off

r79a died at the 150-turn cap with its FIX doc containing only §0 (a clean premise re-check: base broker
**126/128**, the four canaries Equal at base, `allwin` 5 windows `del 1/ins 7` @362, `ins 37` @520, `ins 177`
@522, `del 61` @700..@1210, `del 162` @1890..@2884, plus the `dis.dis` ground truth for the compound
`while (A or B or (C and D))` loop and the admission that its first hand-computed jump dump was WRONG and was
discarded). It left seven analyzer candidates and no measurement table.

I installed its `CANDIDATE_r79a_AB_region_analyzer.py` (sha16 `583506e7035f438a`) over the landed generator
`11324f276cce6d5b` in my own mirror and regenerated broker:

```
[single] status=failure units=126/128 success_rate=98.44%
  ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
```

⇒ **no flip**, banked (`rounds/round39/r79/`, including my product `MEASURED_by_orchestrator_AB_broker_product.py`).
The 5-window table above is also the honest answer to "why is `_sync_worker` not a −3 unit": `delta=-3` is the
*net* of +221 inserted and −224 deleted across five windows — it is a restructured loop body, not a missing
instruction, which is why three separate criteria have now changed nothing the judge can accept.

## 10. Round 39 in one line for the next hand

Ten engineer-runs, 0 flips, ~14 banked candidates with sha16'd builders in `rounds/round39/`. The landed bytes
are still gate 38's (`11324f276cce6d5b` / `f7d849e974904492`, **6614/6617 = 99.9547 %, 400/402 files**),
`git status --porcelain -- core/ site-packages/` = 0, and gate label **39 is unconsumed** — re-run
`gate_chain.py 39 38` after the next flip rather than advancing the label. Two axes remain genuinely untried:
arm-tail emission shape for clock_worker's two spurious `JUMP_FORWARD`s (`@7252`/`@7590`, the `[R21-36]`
family, base `30a4d7827122e165`), and `_process_order`'s two loss classes (ternary-as-CALL-argument reaching
`compile()` with empty arms, plus one whole `strategy_log.info(f'…')` statement missing).


## 11. My own root-cause reading of the last two windows (no engineer available — the 11th dispatch died instantly with no mirror and no python process)

The `r80a` dispatch produced nothing (no `D:/Temp/r80`, zero python processes), so I did the measurement myself in
`D:/Temp/r81` = repo bytes + base `30a4d7827122e165`, regenerated `realtime_event_source`, compiled the product,
and mapped instruction offsets → source lines with `co_lines()`.

**Both "spurious `JUMP_FORWARD`" windows land on the SAME target, prod `@9206`, which is line 216 =
`while self.active:`'s condition re-test** (`LOAD_DEREF self / LOAD_ATTR active /
POP_JUMP_BACKWARD_IF_TRUE 5614`). Mapping the two windows:

```
@7248 POP_JUMP_FORWARD_IF_FALSE -> 7254     line 249   if pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date:
@7250 EXTENDED_ARG 3
@7252 JUMP_FORWARD -> 9206                   line 250       pass
...
@7578 STORE_ATTR pre_before_trading_date     line 259
@7588 EXTENDED_ARG 3
@7590 JUMP_FORWARD -> 9206                   line 259
@7592 LOAD_FAST now_date                     line 260   (sequential code continues)
```

So the residual is NOT an unknown threading bug: it is the **elif-chain end-label law** (r68a) showing up as two
arm tails, and the reason those tails jump is that the emitted chain's end label is the loop re-test — plus, at
line 249-250, our `then` arm is **`pass`**. An empty `then` where the original has the
`system_log.debug('获取重登信号量')` statement is the direct, visible signature of the
`inline_boolop_chains` fold swallowing `@7270` into the condition (`inline_blocks=[7248,7270]`, r78a's census),
and the swallowed `debug()` reappears one arm later at emitted line 248 inside `elif now_date != self.first_run_date:`.

**What this tells the next hand, and it is cheaper than another blind attempt:** the fix is not a suppression rule
for the two jumps (they are the lawful consequence of the flat chain + the loop re-test being its end label). The
fix is to un-swallow the `debug()` statement, which turns line 249's `pass` arm into a real arm and, per the
landed `[R21-43]` precedent, most likely changes the chain's end-label placement too. Concretely: the
condition-context ibc fold must refuse to absorb a member block whose value is consumed by a `POP_TOP`
(discarded call) rather than by a following `POP_JUMP_*` — that is a stack-shape/opcode-class test on the member
block itself, i.e. exactly the "correct at identification" kind the spec allows, and it is a *different* rule from
`[R21-44]` conjunct ⑧ (which refuses whole sites) and from `[R21-49]` (which refused whole chains).
Both of those failed because they deleted or re-parented the chain; this one edits only the fold's membership.

Product bytes for anyone re-checking: `rounds/round39/r81_product_evt_base.py` is NOT committed (my mirror output);
reproduce with `python -X utf8 pycdc.py --region -o out.py <abs pyc>` after installing `30a4d7827122e165`.


## 12. My §11 hypothesis was WRONG in its central claim, and r82a proved it — recorded so nobody re-tries it

§11 said the `inline_boolop_chains` fold swallowed the `system_log.debug('获取重登信号量')` statement, and that the
`pass` arm at emitted line 249–250 was the evidence. r82a measured the same bytes and falsified the causal half of
that: the statement **is** emitted — `system_log.debug(...)` compiles at prod `@7276`, emitted line 252 — because
`[R21-46]` (`_r2146_ibc_member_has_stmt_prefix` + `_r2113_legs_back`, consumed at
`region_ast_generator.py:20577`, i.e. r75a's own banked half that is present in base `30a4d782`) **already refuses
that fold**. What I read correctly: `inline_blocks=[7248,7270]` holds, the `pass` arm holds, and the `debug()` does
reappear one arm later. What I got wrong: concluding the fold deleted the statement. An empty `then` arm is not
evidence of a swallowed statement when a veto already fires — it is evidence the arm is empty *for another reason*.

r82a's measurements (its product byte-identical to my base product, so we measured the same bytes):

| variant | delta | windows | landings | judge | changed files |
|---|---|---|---|---|---|
| base `30a4d7827122e165` | `+2` | 2 | 7 | 12/13 Different control flow | — |
| A: my POP_TOP-membership rule, generator-side (`32595f2b7e21f8b9`) | `+2` | 2 | 7 | 12/13 | **0 / 20** (byte-identical) |
| B: same rule at the analyzer home (r78a's `8d9993219d2f7418`) | `-269` | 4 | 2 | 12/13 | 1 (the target, worse) |

Censuses make the redundancy quantitative: panel 20 files = 246 ibc records / 296 member evaluations, **1 fire**,
`fire_only_new=0`; corpus-wide (406 pyc, analyzer-only) = 570 records / 664 members, **still 1 fire**, and that one
record already satisfies `[R21-46]` ⇒ **the rule has no independent action surface anywhere in the corpus**. Banked,
not installed. Probe inert 20/20. Membership for clock_worker: `regions=67 blocks=191 two_owner=148 zero_owner=14`
identical base-vs-A (note r82a and r78a count `two_owner` by different rules, 148 vs 186 — cite the rule, not the
number, when comparing).

**The real discriminator, handed over by r82a and now the next ticket:** `@7248` is collected as `@7186`'s **elif
condition**, which is what makes the *parent* arm (`IfRegion@7216`) empty and gives the flat chain the loop re-test
as its end label. The proof it is not a genuine elif: `@7248`'s false exit `@7492` lies **inside
`IfRegion@7216.then_blocks` and simultaneously inside `@7186.elif_final_else`** (that 44-block list whose refusal
cost r78a `-269`). Second independent axis it names: `A`'s false exit must land on `C`'s test, i.e. the shape is
`(A and B) or C`. So a *narrower* collection rule than `[R21-49]`'s — one keyed on that shared-block signature
rather than on the whole chain — is the only untried route left on this unit.


## 13. r83a (R21-53) — the narrow shared-exit collection rule is DEAD too: its product IS the −269 collapse

The quota cap killed r83a at ≈21:00 mid-implementation, but it left the full evidence chain, which I re-measured:
three analyzer candidates (`e8782b2787c01667`, `17276fc2b55c1440`, `b7e7ded85a3a8418`) and three products
(`out_fix/`, `out_fix2/`, `out_fix4/`, all 18046 bytes vs the base's 21548).

My readings on those bytes (base is 21548 bytes, `+2 / 2 windows / 7 landings`, judge 12/13):

| product | `unit_diff` | judge |
|---|---|---|
| `out_fix`  | `prod=1155 delta=-269 hunks=4 landings=2` | 12/13 |
| `out_fix2` | `prod=1155 delta=-269` (same)              | — |
| `out_fix4` | `prod=1155 delta=-269`                     | — |

So my §12 handover — "the shared-exit signature is the only untried route" — was wrong: the narrower rule
collapses **identically** to [R21-49]'s whole-chain refusal. The deletion hunks are the same three
(54 @7582..@7836, 55 @7960..@8276, 160 @8282..@9192), i.e. **any** rule that removes `@7248` from
`@7186.elif_conditions` drags the 42-block `elif_final_else` with it and destroys the chain tail.

r83a's premise work is still the most complete statement of the region shape we have, and it corrected two of
my numbers (both accepted): `elif_final_else` is **42** blocks, not 44, and `@7248`'s successors are
`[7270, 7492, 9218]` with true→7270 / false→7492. Its §2c original-bytecode readout also confirms axis 2 of
the ticket exactly: `orig @7184 POP_JUMP_FORWARD_IF_FALSE -> 7216` — `A`'s false exit lands on `C`'s test, i.e.
`(A and B) or C`, and the `@7248` arm's own merge is `@7582` while the chain's merge is `@7216`.

**What is left on this unit after thirteen runs.** The two `JUMP_FORWARD -> @9206` are the single-end-label
consequence of a flat chain whose tail-label is the `while self.active:` re-test, and *every* analyzer-side route
that changes the chain's shape (declare, filter, collect, narrow-collect) collapses to −269/−274. That closes
clock_worker's analyzer routes for this session; the only untried direction is emission-shape nesting for the flat
chain — i.e. re-rendering `@7186` as a nested `else: If(…)` exactly as landed [R21-43] does, rather than refusing
the collection. That is a NEW ticket, not this axis, and it belongs on the generator side.


## 14. GATE 39 WAS RUN AND FAILED ON A COLLATERAL — the pair flips `_process_order` and breaks `replace_utils`; reverted, label 39 unconsumed

I installed the R21-55 pair after verifying the flip in my own mirror (broker **127/128**, `_process_order`
`orig=507 prod=507 delta=0 hunks=0`), ran the full chain (`rounds/round39/gate39_failed/gate_chain_39.log.txt`):

```
[regen 合计] ok=402 bad=0                    191s
[verify 0..7] rc=0  786/786 468/469 538/538 887/887 855/855 998/999 800/801 1282/1282   143s
[units] 6614/6617 -> 6614/6617  (99.9547%)   [files] 400 -> 399
[gates] 文件级回退=1  UNIT_REGRESSIONS=1  新增失败单元=1  翻正单元=1
   FIXED   trade_live_broker.pyc <module>.TradeLiveBroker._process_order      (126 -> 127)
   FILE-BROKE IQCommon/util/replace_utils.pyc  9 -> 8   NEW-FAIL <module>.decrypt_database_url
[quotation] 153/153   [small34] units_success 1566   [selfcheck] 153/153, 变异 1/153 + 1/153
[pytest] 2 failed, 282 passed, 2 xpassed (the two permanent residents, zero new failures)
```

So the flip is real and the regression is real, in the same run. Reverted: `core/` back to
`11324f276cce6d5b` / `f7d849e974904492` and the 402 products restored, because a file-level regression cannot
land. **Gate label 39 stays unconsumed** (the campaign rule: re-run the label after the next candidate).

**Which half, and why — measured in minutes, not guessed.** In my mirror with ONLY the analyzer half
(`842e2748bcdfeb66`) installed, `replace_utils` reads **8/9** ⇒ A is the culprit, the generator half is
exonerated. The text diff against the committed product is 3 lines and says everything:

```
             app_log.info('SM4解密执行完成，解密结果长度: {}'.format(len(decrypted_url) if decrypted_url else 0))
+            decrypted_url            <-- a bare expression statement emitted where nothing is emitted in the original
             if not decrypted_url or '://' not in decrypted_url:
-                return url
+                url                 <-- a RETURN_STATEMENT destroyed: the value is emitted, the `return` is not
```

The diamond-join recovery emits the join block's pushed value as a **statement** whenever it cannot prove the
value is consumed by the join. In `replace_utils` the value is discarded (`POP_TOP`) in the first site and consumed
by `RETURN_VALUE` in the second — so the rule needs a **consumption conjunct** before it may act: it may only
recover a join whose value is actually bound/returned/passed, and must refuse when the consumer is `POP_TOP` or
when the block's own terminator is a `RETURN`. That is the same stack-shape distinction I wrote in §11 for the ibc
fold and it is implementable from opcode class alone.

**Process lesson I am writing down for myself:** r85a's census was sound *for what it counted* (6 fires, all in
`_process_order`) and its 20-file panel was clean, and BOTH were true — yet the corpus broke a file that is not in
the panel. My standing pre-gate panel has to change: before asking for a gate, **regen all 402 products from the
candidate and byte-diff against the committed ones** (no judging needed, ~200 s), then judge only the changed
files. The panel's purpose is to catch collateral, and a 20-file panel by construction cannot catch collateral in
the other 382. Related: `rounds/round38/PANEL_20files.txt` was itself created from residual + canaries, which is
the bias that produced this miss.
