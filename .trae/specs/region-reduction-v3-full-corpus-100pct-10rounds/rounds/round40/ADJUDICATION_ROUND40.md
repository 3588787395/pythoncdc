# ADJUDICATION_ROUND40 — measured record of round 40 (gate label 40, input `rounds/round39/after`)

Standing state at the opening of this record: landed generator `b4363f5858e58074`, landed analyzer `842e2748bcdfeb66`,
corpus **6615/6617 (99.9698 %)**, **400/402 files**, residual 2 files / 2 units
(`realtime_event_source.clock_worker` 12/13, `trade_live_broker._sync_worker` 127/128). Gate label 40 unconsumed.
Every number below is either my own measurement in `D:/Temp/r91m` (fresh mirror, landed bytes verified by sha16
before use) or an engineer reading I re-measured. Nothing here is a plan.

## 1. The clock_worker "platform" was contaminated, and my certification of it was the error

`rounds/round40/MEASURE_R21-58_reanchor_by_orchestrator.md` (addendum 1). I installed the re-anchored chain
`db1f0e96072cdcb3` alone over the landed analyzer, regenerated, and judged:

| file | HEAD control | re-anchored chain |
|---|---|---|
| `plugin_system_risk_calculation/function.pyc` | **15/15 `status=success`** | **14/15**, `create_daily_stats: Different control flow` |
| `realtime_event_source.pyc` | 12/13 | 12/13 (clock_worker `delta=+2 / 2 windows / 7 landings`, unchanged) |

The lost code is a whole statement run (`unit_diff` `del=32 ins=0` at `@196..@336`): inside a `for … else:` body, the
three `period_*` assignments and the `break` that follow a nested `if/else` are not emitted at all, the container's
header test becomes `JUMP_BACKWARD` instead of `JUMP_FORWARD` (`@138`), and because the locals are never assigned,
three later reads flip `LOAD_FAST period_close/label/open` → `LOAD_GLOBAL` (`@680/@684/@688`). A dropped statement
sequence therefore also changed *scope* — which is why the judge calls it a control-flow difference rather than a
text difference.

**Withdrawal, in the record:** my round-39 statement that "the re-anchored chain base is inert" was based on judging
broker, `replace_utils` and `quote` — three files, not the corpus. The 402-product CR-stripped sweep is what caught
this, exactly as it caught `replace_utils` at gate 39 attempt 1.

## 2. Attribution and recovery of the platform (r88a, r92a; both re-measured by me)

r88a's step-wise ablation (each row resets BOTH core files, both sha16s logged) put the contamination in **step 1** of
the chain and in one of its two halves only:

| row | generator | `function.pyc` | clock_worker |
|---|---|---|---|
| landed | `b4363f5858e58074` | 15/15 | −113 |
| step1 P1+P2 | `411c2bd948cd33ad` | **14/15** | −6 |
| `[R21-24-M1]` alone | `e5849f71a6682aa1` | **15/15** | −6 (all of step 1's gain) |
| `[R21-38-r63a]` alone | `1e1e0cdeecf7957b` | **14/15** | −113 (buys nothing alone) |
| +`[R21-45]`/`[R21-44]`/`[R21-46]` | `945ffcd0…`/`07deef97…`/`db1f0e96…` | 14/15 | −4 / −5 / **+2** |

and the regression predates gate 39 (`cf5868e68208adf6`, `30a4d7827122e165` on gate-38 bytes also read 14/15): the
file simply is not in `rounds/round38/PANEL_20files.txt`, so no 20-file reading could ever have seen it.

r92a then localized it to one hunk (**H3**, a claim-without-emission branch) and added a conjunct that requires the
entry list the emission underneath already consumes. I re-measured that candidate myself over the landed analyzer:

| file | landed | full chain `db1f0e96` | **`[R21-63]` `675ec7afa414bbb5`** |
|---|---|---|---|
| `function.pyc` | 15/15 | 14/15 | **15/15** |
| `realtime_event_source.pyc` | 12/13 | 12/13 | 12/13, sole failure still `clock_worker` |
| `replace_utils.pyc` | 9/9 | 9/9 | 9/9 |
| `trade_live_broker.pyc` | 127/128 | 127/128 | 127/128, sole failure `_sync_worker` |

r92a's own 402-product sweep reads `CHANGED=1` (the target only) versus the chain's `CHANGED=2`.
**Conclusion: the chain is now a safe platform and still buys zero flips** — banked, not installed.

Shape note from my rig on the narrowed chain: `clock_worker`'s whole loss becomes **6 spurious insertions in 4
windows** (`@7184 +1`, `@7248 +2`, `@7582 +2`, `@7602 +1`) with no deletion window — all of them the arm-tail
`JUMP_FORWARD`s landing on the `while self.active:` re-test.

## 3. Axes closed with verdicts this round (no re-run)

1. **R21-60 arm ordering / fall-through for `clock_worker` — FALSIFIED (r89a).** The rendered arm order already equals
   the original's evaluation order (`7186/7202/7216 → 7248 → 7582`), so permuting arms only moves ~15 already-aligned
   test instructions. Census over **1269 `IF_ELIF_CHAIN` regions in all 402 files**: `FIRE=1` in
   `klinedata::_all_bars_of_cache` (that file is already 64/64), `FIRE=0` in `clock_worker`; class
   `BOUNDARY_ONLY`, and under the chain's true end label `9194` (the original has exactly 6 jumps there) the law
   *demands* both spurious jumps — one chain has one end label and one fall-through arm, so no tail choice reproduces
   the original's two fall-throughs. The residual belongs to the chain-boundary/fold surface (`[R21-49]`/`[R21-53]`,
   previously measured at −269), not to arm order.
2. **Chained comparison in `_sync_worker`'s loop condition — FALSIFIED twice, independently.** My opcode census:
   `COMPARE_OP` parity 21/21 and the product renders **more** chained compares than the original (3 vs 2). r90a's
   detector run: 54 evaluations, 2 fires, **both in the second loop**, and the failing window `@232..@1212` contains
   **zero** `SWAP`/`COPY`.
3. **Per-exit-edge duplication for `_sync_worker` — FALSIFIED** by the same window analysis: the 165-instruction
   "deleted" span and the 166-instruction "inserted" span are the *same* loop body relocated ~1100 offsets, so nothing
   is unrendered.

## 4. The duplicated-while-test law, and the GOLD oracle that proves the unit reachable

Measured law on this interpreter (3.11.7), from `compile()` + `dis`: a `while <BoolOp>:` condition is emitted **twice**
— an entry copy above the body whose legs jump *forward* to the body-start block (last leg forward to the exit), and a
latch copy below the body whose legs jump *backward* to that same body-start block. Template
`while a or b or c: x = x + 1`: `@4/@8 FORWARD_IF_TRUE 14`, `@12 FORWARD_IF_FALSE 36`, body at `14`, then
`@26/@30/@34 BACKWARD_IF_TRUE 14`. Corollaries: an N-leg or-chain yields N−1 backward conditional edges onto the body
start, and a `continue` is an **unconditional** `JUMP_BACKWARD`, so a backward *conditional* edge is never a continue.

The original `_sync_worker` matches edge-for-edge (`@704` = body start beginning `time.sleep(60)`, entered forward from
`@232/@364/@700` and backward from its own tail, `@876`, `@1056`; merge `@1214`), and r90a/r91a each reproduced it from
a control `compile()` independently.

**GOLD oracle** (`rounds/round40/r91/broker_GOLD_PROOF.py`, judged by me):

```
[single] status=success units=128/128 success_rate=100.00%
```

with my rig at 408 instructions vs the original's 412 in 4 small windows (`@542 +1`, `@696 −1`, `@700..@702 −2`,
`@1210..@1212 −2`). Its loop text is one nested loop, `while A or B or (C and not D): time.sleep(60)`, inside the
outer `while True:`. This is evidence and a target only — a hand-spliced product can never be shipped; the pipeline
must produce it.

Where the pipeline stops today (r91a's analyzer candidate `241905c2078f0270`, generator untouched; I re-measured it
over the narrowed `[R21-63]` generator: broker still 127/128, `_sync_worker` 400 instructions, 5 windows):
`_detect_while_condition_boolop_chain(@232)` returns length 1 because the chain head's fall-through `@364` is owned by
the enclosing `while True` region and `interrupts_boolop_forward_chain` vetoes the walk
(`region_analyzer.py:28155-28157`), so Step 5's `len(chain) >= 2` (`:26951-26953`) skips the fold; `all_same_target`
(`:28189-28201`) is structurally unsatisfiable for an or-head + and-tail because `@522` jumps to the loop exit `@702`
while `@232/@364` jump to the header `@704`; `[R7-B45]` covers only and-head + or-tail, which is why
`_detect_while_condition_nested_and_or_chain` returns None at `:28288`; and the latch copy's legs are members of
`loop.body_blocks`, so `_loop_generate_while` renders them as statements. With the chain mounted by r91a's analyzer the
remaining blocker is measured: the generator consumes only `[232,364]` and leaves `IfRegion@522/@544` as siblings.

Collateral estimate is not a guess: predicate **P** (a `LoopRegion` whose header receives a forward conditional jump
from outside its own block set **and** a backward conditional jump from inside `body_blocks`) was censused over
**82** loop conditions in the 20-file panel and **173** across all 402 files and fires **exactly once in both scopes**
— on `_sync_worker`. Owner-counting rule (which reconciles my earlier 148-vs-186 discrepancy): a leg claimed by the
enclosing loop is `two_owner` for the inner loop, not unowned.

## 5. Tooling corrections recorded this round

- My `win_r91.py` aligns on **opcode names only** (shifted jump operands cannot inflate windows) and is
  positive-controlled: the two landed-Equal units `_process_order` and `_process_cancel_order` both read
  `windows=0`. It counts 1442 original instructions for `clock_worker` where `unit_diff`/`allwin` count 1424, so its
  `delta`/window numbers are **not interchangeable** with the engineers'; only the judge reading certifies.
- `git archive HEAD` over the whole repo fails to extract in a scratch dir (`Can't unlink already-existing object` on
  deep `.trae/...` paths). Scope it: `git archive HEAD site-packages | tar -x`, or compare per file with
  `git show HEAD:<path>`. Never `cmp` a regenerated product against a checked-out one (checkout CRLF vs blob LF makes
  every file read as a diff).
- A background push loop that greps the log for `-> branch` is unfalsifiable if the pattern starts with `-`
  (`grep: unknown option`). Verify by `git rev-list --count origin/<branch>..HEAD == 0` instead; that is how the
  round's commits were confirmed (`PUSHED_BY_REF`).

## 6. Open at the time of this writing

Engineers r93a (analyzer: generalize the while-condition chain assembly per `r90a` §8) and r94a (generator: consume the
mounted chain and drop the latch copy, target = GOLD) are running. Nothing has been installed this round; `git status
--porcelain -- core/` = 0 lines and no `*OK.py` is dirty.
## 7. State at 2026-10-13 10:31 (sealing time; roster: sections 1-7 above, all numbers measured by me or re-measured by me)

Nothing installed this round: landed bytes still generator `b4363f5858e58074` + analyzer `842e2748bcdfeb66`,
corpus still **6615/6617 (99.9698 %)**, **400/402 files**, residual **2 files / 2 units**, **gate label 40
unconsumed** (correct under the standing rule that a zero-flip candidate does not consume the label).
`git status --porcelain -- core/` = 0 lines and `-- site-packages/ | grep OK.py` = 0 lines.

Banked this round, each with my own re-measurement: `[R21-63] 675ec7afa414bbb5` (chain collateral removed, zero
flips), `R21-64` analyzer `1471c92eca157e46` (loop-1 fold byte-identical to GOLD, windows 9->6, P fires 1/173,
402-product sweep `CHANGED={trade_live_broker}`), `R21-62` analyzer `241905c2078f0270` (superseded by R21-64 - and my
two attempts to union them failed `merge_hunks.py`'s faithfulness proof in both orders), `R21-60` falsified by census,
`R21-59` addenda 6-16 (the duplication law, GOLD at 128/128, the three-mechanism decomposition, loop 2's P-negative
edge set), `R21-68` clock_worker diagnosis (predicate C = 1 unique region in 1 file; the flip blocked at site 2).

What a flip still requires, stated as the round's honest remaining distance: `_sync_worker` needs loop 2's sibling
predicate (single-comparison loop test: unconditional forward entry + conditional backward latch), the removal of the
folded condition's leftover operand statement, and the reconnect arm's `RETURN_VALUE` (`@1874`) rendered as a return
rather than a loop exit - three separable halves, two of them still running as r95a/r98a/r96a. `clock_worker` needs
predicate C's identification fix *and* a way to isolate site 2 that does not join the -269 over-fire class. Neither
unit is expressible as a one-rule flip, which is why round 40 banks rather than lands.
## 8. Landing criterion calibrated (2026-10-13 10:36)

`rounds/round40/orchestrator/gold_diff_r91m.py` counts unified-diff hunks between a candidate product and the GOLD
text of a unit; 0 hunks means the product *is* the text I judged `status=success units=128/128`. Three controls run
now: GOLD vs GOLD = **0**; the landed product vs GOLD = **4 hunks** (54 vs 45 lines); r93a's folded product vs GOLD =
**3 hunks** (43 vs 45 lines, the three facts of addendum 18); and `_process_order` under the fold vs GOLD = 0, which
is the sanity case since that unit is Equal on both sides. So the measured remaining distance for `_sync_worker` is
exactly those 3 hunks, and the merged candidate is accepted only at 0.
## 9. The pair `1471c92e` + `0f4c3898` measured in my mirror: 2 hunks from the 128/128 text (2026-10-13 10:42)

r95a delivered generator `0f4c3898298e6f2e` (3 hunks inside `_loop_generate_while`'s chained-compare suppression,
`region_ast_generator.py:8126-8174`, gated by `is_chained_compare_cond`), censused at 1 reachable LoopRegion in the
panel and 1 in all 402 files (`loop@1890`), with the same 82/173 condition population r90a measured independently. It
also corrects r91a's mechanism claim: the `sync_data_flag = 1` half was an **over-fire** of the landed `_is_recheck`
("post-store contains a compare op"), which hoisted `@2214`'s store and deleted its `if`.

My own reading of the PAIR (r93a's analyzer + r95a's generator, both hashed after copy):

```
[installed] gen=0f4c3898298e6f2e ana=1471c92eca157e46
[repro]     Different bytecode 1/2        [battery]  RED=8/9
[broker]    units=127/128, sole failure _sync_worker, windows 9 -> 5
[panel]     realtime 12/13  replace_utils 9/9  function 15/15  quote 92/92  quotation 153/153  order_api 37/37
gold_diff   ours=42 lines GOLD=45  hunks_vs_GOLD=2   (@@ -18,0 +19,8 @@  and  @@ -37,5 +44,0 @@)
```

So the distance to a flip is now two textual facts, each with an owner: the reconnect block's nesting plus `return`
(r99a, replacing r96a which died at the turn cap with bytes that scored worse - 4 hunks, because they build on the
landed analyzer and lack the fold), and five lines we emit that GOLD does not (r98a, the leftover latch/operand
statements). Both halves are measured zero-collateral in their own sweeps (`changed = trade_live_broker` only), and
neither flips alone, which is why the gate label stays unconsumed until the union is measured at
`units=128/128`.
## 10. The two remaining hunks are ONE statement (2026-10-13 10:44) - the flip path is `1471c92e` + `0f4c3898` + the reconnect move

I printed our pair's product and GOLD side by side for the whole unit. Every line matches except the reconnect
statement, which we emit **after** loop 2 (ours lines 37-41) as a flat `if A and B and (…) and C:` ending in `break`,
while GOLD emits it **between loop 1 and loop 2** (GOLD lines 19-26) nested four deep ending in `return`. That is the
whole of both hunks: `@@ -18,0 +19,8 @@` is GOLD's 8-line nested version at the right place, and `@@ -37,5 +44,0 @@`
is our same 5 lines in the wrong place. So loop 2's body, latch and `sync_data_flag` guard are now **byte-identical to
GOLD under the pair** - r95a's half closed them - and the unit's distance to `128/128` is a single statement's
position plus terminator class, owned by r99a.

Consequence for the other live engineer: r98a's leftover-operand work is still real for the 12-line repro (which reads
`Different bytecode 1/2` under the pair, i.e. the synthetic loop-2 latch copy is still emitted), but it is **not on the
broker flip path**. I keep it running as the generality check, and the merge plan is: install
`ana 1471c92e` + `gen 0f4c3898` + r99a's reconnect half, require `gold_diff` = 0 hunks and judge
`units=128/128` before touching the repo, then run `gate_chain.py 40 39`.
