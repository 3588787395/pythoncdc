# FIX R21-60 — arm ORDER inside the flat chain, decided by which arm exits at the chain's end label

Unit: `<module>.RealtimeEventSource.clock_worker` (`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`)
Mirror: `D:/Temp/r89` — base `core/cfg/region_ast_generator.py` = **db1f0e96072cdcb3** (`D:/Temp/r88/work/REANCHORED_r2158_db1f0e96072cdcb3.py`),
`core/cfg/region_analyzer.py` = **842e2748bcdfeb66** (gate-39 landed). Repo never written to.

## 0. Base re-measured (rule 6 — every claim in the brief re-measured by me)

| claim in brief | my measurement | verdict |
|---|---|---|
| clock_worker `len orig=1424 prod=1426 delta=+2` | `work/allwin_r63.py` → `len orig=1424 prod=1426 delta=2`, `hunks=2` | CONFIRMED |
| 2 unfiltered windows | hunks #1 insert `prod[1046..1047]` (@7252 JUMP_FORWARD), #2 insert `prod[1100..1101]` (@7590 JUMP_FORWARD) | CONFIRMED |
| 7 landings | `work/UNITDIFF` reproduced from r88: 7 `~` jump-target rows, `judge_diff=True` | CONFIRMED (r88 log + my own target walk, §3) |
| judge `status=failure units=12/13`, product 21548 bytes | `pyc_verify single` → `[single] status=failure units=12/13 success_rate=92.31%`, only failing unit `***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow`; product `D:/Temp/r89/out/prod_base_evt.py` = 21548 B, no BOM, 365 CRLF lines, `\r\r\n`=0 | CONFIRMED |
| `@9206` is line 216 `while self.active:`'s condition re-test | original: `@9194 LOAD_DEREF self / @9196 LOAD_ATTR active / @9206 EXTENDED_ARG / @9208 POP_JUMP_BACKWARD_IF_TRUE -> 5614`, `co_lines` attributes 9194/9196 to **orig line 399** (= product line 216). The chain's end label = block **7194→9194** and 6 original `JUMP_FORWARD -> 9194` exist at 8348/8546/8590/8850/8902/9142 | CONFIRMED |

## 1. Premise check — the rendered arm order vs the original's evaluation order (THE finding)

Rendered chain (from `ast` of the base product; `outer if` = product L248 `if now_date > self.pre_before_trading_date:`):

| arm | product line | test | body | next |
|---|---|---|---|---|
| arm0 | L249 | `pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date` | L250 `pass` (1 stmt) | `elif` L251 |
| arm1 | L251 | `now_date != self.first_run_date` | L252..L259 (2 stmts) | `elif` L260 |
| arm2 | L260 | `now_date > self.before_trading_date` | L261..L309, **no orelse** → falls through | end |

Original evaluation order of those same tests (block starts, from the CFG of the pyc):
`7164 (A)` → `7186+7202 (B, chained)` → `7216 (C)` → `7248 (D)` → `7582 (A2)` → `7604+7620 (B2)` → `7634 (C2)` → `8592` → `8666` → `8904`.

**The rendered arm order is already identical to the original's evaluation order** (B∨C, then D, then A2∨B2∨C2, …). No permutation of these arms reproduces
the original's instruction stream, because permuting the arms permutes the test instructions, which are currently aligned 1:1 with the original's
(`unit_diff` has only the 2 inserted jumps and 7 target rows — every other one of the 1424 instructions matches positionally).

Successor data that closes the ticket's law against this unit (`work/armexit_census.py`, region `IfRegion@7186`, `region_type=IF_ELIF_CHAIN`,
`condition_block=7186`, `then_blocks=[7212]`, `elif_conditions=[7248]`, `elif_bodies=[[7372,7488]]`, `elif_final_else=[7492,7582,…42 blocks]`, `merge_block=7216`):

| arm | arm blocks | normal exit (block successors leaving the arm) | is it the chain's end label 9194? |
|---|---|---|---|
| arm0 (`pass`) | 7186,7202,7212 (+7216 folded as `or`) | **7216** = arm0's own merged-test block, i.e. the block the *fold* continues into; then 7248 = arm1's TEST entry | NO (and not 9194) |
| arm1 (`elif D`) | 7248,7270,7372,7488,7492 | **7582** = arm2's TEST entry (7488 is `RETURN_VALUE`, no exit) | NO |
| arm2 (last, final else tail) | 7492…9144 | **9194** = loop latch = the chain's end label | YES |

Consequences, both decidable from the table:

1. The ticket's rule — *"the arm whose normal CFG exit is the chain's end label is the one rendered last; the others must jump"* — **is already
   satisfied** by the current rendering: exactly one arm (arm2) exits at the end label, it is last, and the two arms whose exits are not the end
   label (arm0, arm1) are the two that jump. The rule fires **0** times here; it cannot remove the two `JUMP_FORWARD`s, it *demands* them.
2. The original's arm0/arm1 exits are **another arm's test entry** (7248, 7582), not a merge label at all. A real `if/elif/else` chain has ONE end
   label and every non-last arm exits at it (r68a's law), so an arm that exits at the *next arm's test* cannot be an arm of that chain — under the
   law's own vocabulary the two arms are not mis-ordered, they are **mis-membershiped**. Two arms both exit inside the chain's own test sequence, and
   only one arm can ever be the tail, so no ordering decision (any permutation, any tail choice) reproduces the original: the second one still needs
   a jump.
3. Reading the original back out of the CFG, the true source shape at this level (loop body, orig lines 469-483) is
   ```
   469: if (now_date > self.pre_before_trading_date and pre_before_trading <= now_time < pm_close
   470:         or self.pre_before_trading_date == self.initial_trading_date):
   472:     if now_date != self.first_run_date:                      # NESTED, not elif
   473:         system_log.debug('获取重登信号量')
   474:         if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:
   475-477:   system_log.error(...); self.event_queue.put(...); return
   478:     self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))   # SIBLING (dedented), 7492
   479:     self.pre_before_trading_date = now_date                          #            preds = {7248, 7270}
   482: if (now_date > self.before_trading_date and before_trading <= now_time < pm_close
   483:         or self.before_trading_date == self.initial_trading_date):   # SEPARATE statement, then genuine elifs
   ```
   Evidence: block `7164`'s false edge is `7216` (mid-test, the `or` continuation) not a body; `7216`'s true edge is `7248` (the nested `if D`) and its
   false edge is `7582` (the next *statement*); `7492`'s predecessors are exactly `{7248 (D false), 7270 (acquire false)}` — the signature of a sibling
   after a then-branch ending in `return`, not of an `else`; `7582` is reached by fall-through from `7492` and by `7216`'s false edge.
   Our product instead folds `A` out (`if A:` L248) and renders `(B or C)`/`D`/`A2` as one 3-arm chain.
   So the two extra `JUMP_FORWARD`s and 5 of the 7 landings are all **one** cause: the chain boundary + the `(A and B) or C` fold, i.e. nesting /
   membership — the axis the brief already closed via `[R21-49]` whole-chain refusal and `[R21-53]` narrow shared-exit refusal (both −269, because
   `@7186.elif_final_else` is 42 blocks = the whole function tail).

## 2. Fire census BEFORE editing (rule 2)

See §4 (v2 census, terminal-class based). A first pass `work/armexit_census.py` counted "an arm's exit set contains the end
label" — that is not the law (a non-last arm JUMPS to the end, so its exit set legitimately contains it) and it reported 93
spurious fires over the panel; it is kept only as the superseded instrument (`work/CENSUS_armexit_panel20.txt`).

## 3. Landing walk (my own measurement, whole-module `compile()` of the base product)

Filtered-index walk of the compiled product unit (same `DROP` as `unit_diff.dump`):

```
idx 1045 @7248 POP_JUMP_FORWARD_IF_FALSE -> 7254   L249   arm0 test (`B or C`) false -> arm1 TEST
idx 1046 @7252 JUMP_FORWARD              -> 9206   L250   MANUFACTURED 1 (arm0 body = `pass`)
idx 1047 @7254 LOAD_FAST now_date                   L251   arm1 test
idx 1099 @7578 STORE_ATTR pre_before_trading_date   L259   arm1 body last instruction
idx 1100 @7590 JUMP_FORWARD              -> 9206          MANUFACTURED 2 (arm1 body end)
idx 1101 @7592 LOAD_FAST now_date                   L260   arm2 test
idx 1392 @9206 LOAD_DEREF self                    L216    <- both manufactured targets
idx 1393 @9208 LOAD_ATTR  active                  L216
```

`@9206` = the `while self.active:` condition re-test **confirmed by me**, and both manufactured jumps land there.
Original-side census of the same end label (`work/orig_chain_dump.txt` + whole-unit `dis` walk): the original contains exactly
**6** `JUMP_FORWARD -> 9194` (the same latch block in orig numbering) at offsets 8348, 8546, 8590, 8850, 8902, 9142, and **no**
jump at the two places our product jumps (between `@7246 C-false` and `@7248`, and between `@7572 STORE_ATTR` and `@7582`).

## 4. Fire census BEFORE editing (rule 2)

Counting rule stated in `work/armexit_census2.py`: arms = `then_blocks` + non-empty `elif_bodies[i]` + `elif_final_else`;
end label = `region.merge_block`; each arm is terminal-classified from its own block terminators
(`JUMP_TO_END / FALL_TO_END / JUMP_TO_OTHER / FALL_TO_OTHER / NO_EXIT / COND_ONLY / INTERNAL_ONLY`).
`FIRE_TAIL` = the ticket rule has work to do: some **earlier** arm falls through onto the chain's end label while the **last**
arm does not.

| scope | regions | blocks | EVAL (IF_ELIF_CHAIN) | **FIRE_TAIL** | OK_TAIL | BOUNDARY_ONLY | TWO_FALL_END | UNCLASSIFIED | NO_END_LABEL |
|---|---|---|---|---|---|---|---|---|---|
| target file only (`CENSUS_armexit2_evt.txt`) | 88 | 226 | 5 | **0** | 0 | 2 | 0 | 3 | 0 |
| 20-file panel (`CENSUS_armexit2_panel20.txt`) | 8344 | 12291 | 552 | **1** | 91 | 16 | 0 | 356 | 88 |
| 402-file roster (`CENSUS_armexit2_corpus.txt`) | 26480 | 37629 | 1269 | **1** | 229 | 27 | 0 | 751 | 261 |

The single corpus-wide fire is `site-packages/IQCommon/api/klinedata.pyc :: _all_bars_of_cache` (cond=148 end=250,
`arms=[('then',['INTERNAL_ONLY']),('elif0',['COND_ONLY','FALL_TO_END']),('final_else',['JUMP_TO_END'])]`). That file is
**already green** — `pyc_verify single` reads `status=success units=64/64` on BOTH the committed product and the base-swept
product — so acting on the only fire can only move a passing file, and it is not our unit. Our region classifies
`BOUNDARY_ONLY`, never `FIRE_TAIL`:

```
CHAIN clock_worker cond=7186 end=7216 arms=3
  [('then', ['JUMP_TO_END']), ('elif0', ['INTERNAL_ONLY']), ('final_else', ['FALL_TO_OTHER:9194','JUMP_TO_OTHER:9194'])]
```

## 5. VERDICT — arm ORDER is not the lever on this unit (the ticket's escape clause, with numbers)

1. **The rendered arm order already equals the original's evaluation order.** Product arms: `B or C` (L249 = orig blocks
   7186/7202/7212 + 7216 folded), `D` (L251 = orig 7248), `A2` (L260 = orig 7582). Original test order: 7164 A, 7186/7202 B,
   7216 C, 7248 D, 7582 A2, 7604/7620 B2, 7634 C2, 8592, 8666, 8904 — the same sequence. A chain emits its tests in source
   order, so any permutation of these arms permutes the ~15 test instructions that currently align 1:1 with the original
   (`unit_diff` shows only 2 insertions across 1426 instructions). Rotation cannot shrink the diff, only grow it.
2. **With the true end label (9194 = the `while self.active:` latch) the law is already satisfied**: exactly one arm — the last
   (`final_else`) — exits at 9194; arm0 exits at 7216 and arm1 exits at 7582, so the law *demands* a jump on both, which is
   precisely the two `JUMP_FORWARD`s that remain. Fires on the unit = **0**.
3. **With the analyzer's `merge_block` (7216) as the end label**, the only arm that exits at the end label is arm0, and it does
   so via an unconditional `JUMP_FORWARD` (7212 -> 7216), which the law permits for a non-last arm => still no fire
   (`FALL_TO_END` on an earlier arm is required for the rule to act). And 7216 is not a chain end at all — it is the `or`
   continuation test block of the enclosing BoolOp — so that reading would rotate the 42-block function tail above arm0, i.e.
   the same edit surface already measured at **-269** by `[R21-49]` whole-chain refusal / `[R21-53]` narrow shared-exit refusal.
4. Two different arms (`B or C` and `D`) both fall through in the ORIGINAL, each onto the **next arm's test entry**
   (7216 -> 7248; 7492 -> 7582). A CPython if/elif/else chain has ONE end label and exactly ONE fall-through arm, so no tail
   choice inside a single chain reproduces both. The residual is a **chain-boundary / BoolOp-fold** defect: the original is
   `if (A and B) or C: (if D: … ; put; assign)` followed by a SEPARATE `if (A2 and B2) or C2: … elif …` chain (§1 evidence:
   `preds(7492) = {7248, 7270}`, `7216 false -> 7582` = next statement, `7164 false -> 7216` = mid-test).
   **No `[R21-60]` code change is installed in the candidate; the candidate bytes are the base bytes** (`db1f0e96072cdcb3`),
   and the sweep below is therefore the pending 402-file collateral evidence for the base itself.

## 6. Mandatory pre-install collateral sweep — the base FAILS it

Mirror `D:/Temp/r89`, gen `db1f0e96072cdcb3` + ana `842e2748bcdfeb66`. All 402 roster pyc regenerated (`work/sweep.py`:
chunk 1 `BUDGET NEXT=372 ok=372 bad=0`, chunk 2 `SWEEP done ok=30 bad=0 elapsed=24s`; 402/402 products, 0 bad, ~150 s total).
CR-stripped byte-diff vs `git archive HEAD` (`head/`, 407 committed products):
**compared=402 identical=400 CHANGED=2 missing=0** (`work/SWEEP_r89a_cmp.log`).

Per-changed-file judge lines (`work/JUDGE_changed_r89a.txt`, `pyc_verify single` on the same bytes):

| file | HEAD (gate-39 committed) | R89a base sweep | verdict |
|---|---|---|---|
| `…/plugin_system_event_source/realtime_event_source.pyc` | `status=failure units=12/13` (clock_worker) | `status=failure units=12/13` (same single failing unit) | target file, **no flip**, no decrease |
| `…/plugin_system_risk_calculation/function.pyc` | **`status=success units=15/15`** | **`status=failure units=14/15`** — `***<module>.create_daily_stats: Failure: Different control flow` | **CORPUS REGRESSION in a file outside the 20-file panel: files 400 -> 399, units 6615 -> 6614** |
| `…/plugin_system_trade/trade_live_broker.pyc` | 127/128 (`_sync_worker` only) | 127/128 (`_sync_worker` only) | byte-identical, inert |
| `IQCommon/util/replace_utils.pyc` | 9/9 | 9/9 | byte-identical, inert |
| `fly/data/quote.pyc`, `fly/data/quotation.pyc`, `…/fly_api/order_api.pyc` | 92/92, 153/153, 37/37 | 92/92, 153/153, 37/37 | byte-identical, inert |

The complete `function.pyc` product diff (HEAD vs base, CR-stripped — one hunk, 4 lines):

```
             else:
                 daily_dts = [local_to_utc(daily_result[account]['date'])]
-            period_close = daily_result[account]['date'].strftime('%Y-%m-%dT07:00:00.000Z')
-            period_label = daily_result[account]['date'].strftime('%Y-%m')
-            period_open = daily_result[account]['date'].strftime('%Y-%m-%dT01:31:00.000Z')
-            break
     else:
```

Half-by-half attribution (rule 3 — every row resets BOTH core files and prints BOTH sha16s; `work/ABLATE_function_halves.txt`;
unit = `function.pyc`, product bytes are the CRLF output of `pycdc.py --region`):

| chain stage | gen sha16 | ana sha16 | product B | judge |
|---|---|---|---|---|
| landed gate-39 | b4363f5858e58074 | 842e2748bcdfeb66 | 30095 | **status=success 15/15** |
| r73a P1+P2 on g39 | 411c2bd948cd33ad | 842e2748bcdfeb66 | 29815 | **14/15 — `create_daily_stats` fails** |
| + r74a [R21-45] A+B | 945ffcd098db6b00 | 842e2748bcdfeb66 | 29815 | 14/15 (unchanged) |
| + r73a [R21-44] | 07deef97054dbadb | 842e2748bcdfeb66 | 29815 | 14/15 (unchanged) |
| + r75a [R21-46] A+B (= base) | db1f0e96072cdcb3 | 842e2748bcdfeb66 | 29815 | 14/15 (unchanged) |
| REANCHORED_r2158 (= base) | db1f0e96072cdcb3 | 842e2748bcdfeb66 | 29815 | 14/15 (unchanged) |

=> The collateral is created by the **first** stage (r73a `P1+P2`, gen `411c2bd948cd33ad`) and no later stage repairs it (the
`function.pyc` product is byte-identical from stage 1 onward). `tmp2_r75.py` and `REANCHORED_r2158_…py` are the same bytes
(`db1f0e96072cdcb3`), so the re-anchor is byte-faithful; my own clock_worker reproduction (12/13, delta +2, 2 windows,
21548-byte product) confirms the base is the brief's base.
**Gate consequence: the base is not installable as it stands** — it honours the "three highest-risk files inert" claim but
breaks a fourth file the panel does not cover, the exact failure mode the round-39 adjudication introduced this sweep to catch.
A fix for that regression belongs to the `P1+P2` half (r73a), not to R21-60.

Killing numbers for that regression (`work/allwin_r63.py`, unit `<module>.create_daily_stats`, base-swept product):
`len orig=480 prod=448 delta=-32`, 2 windows — #1 `@138 JUMP_FORWARD` becomes `JUMP_BACKWARD`, #2 deletes 32 instructions
(`@196..@396`: the three `period_*` strftime statements plus the `break`). So `P1+P2` turns a loop body into a loop latch and
drops its tail: a |delta|=32 structural loss, not a small-window artifact. That is the ticket the next hand should open
(r73a P1/P2 boundary on `create_daily_stats`), and it gates the base independently of R21-60.

## 7. Rule-1 membership numbers (counting rule stated)

No code was changed and the candidate's analyzer bytes are identical in base and candidate (`842e2748bcdfeb66`), so membership
is identical by construction; regions/blocks are analyzer-level and were re-measured on the candidate mirror. Counting rule: a
block is **role-claimed** once per region role list that names it (`condition_block`/`entry`/`header_block`/`then_blocks`/
`else_blocks`/`body_blocks`/`elif_final_else`/`elif_bodies[i]`/`try_blocks`/`finally_blocks`/`handler_blocks`);
`region.blocks` (the descendant hull) is deliberately NOT used — that is the definition behind this week's 148-vs-186.

| scope | regions | blocks | zero_role_owner | two_role_owner (>1) |
|---|---|---|---|---|
| target file | 88 | 226 | 9 | 196 |
| 20-file panel | 8344 | 12291 | 1530 | 8324 |
| 402-file roster | 26480 | 37629 | 5471 | 20424 |

## 8. Deliverables / files

`DELIVER/FIX_R21-60_clock_worker_arm_order_fallthrough.md` (this), `DELIVER/build_cand_r89a_r2160.py`,
`DELIVER/products/PROD_base_evt_21548.py` (measured product), `DELIVER/CENSUS_armexit2_{evt,panel20,corpus}.txt`,
`DELIVER/SWEEP_r89a.log`, `DELIVER/SWEEP_r89a_cmp.log`, `DELIVER/JUDGE_changed_r89a.txt`,
`DELIVER/ABLATE_function_halves.txt`, `DELIVER/orig_chain_dump.txt`, `DELIVER/armexit_census2.py`.
