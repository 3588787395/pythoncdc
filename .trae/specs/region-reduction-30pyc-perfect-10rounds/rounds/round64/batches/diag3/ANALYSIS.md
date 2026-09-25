# ANALYSIS.md — Round 64, diag3 (DIAGNOSE ONLY)

Companion to `FACTS.md` (baselines, measurements, replay commands). All landed-byte
numbers there were re-derived on sha `c694d2514eb2f2b21ccf` / `7ec41fa2f9cdd5d62c1a`.

Conventions used below:
* "offset" = `BasicBlock.start_offset` / instruction offset in the ORIGINAL code object.
* `align_*.txt` = `logs/align_<func>.txt`, produced by `align.py` (difflib on the
  decompiled *re-executed* instruction stream vs the original stream; index-aligned,
  so a hunk near the tail is usually an index shift, not a defect).
* Region dumps = `logs/probe_cbb2_*.txt` (produced by `probe_cbb2.py`, which logs every
  `RegionAnalyzer._collect_branch_blocks` call and then prints the final region forest).

---

## §1 D1 — `trade_info_utils :: trade_operation`: post-if join block claimed by a nested else arm
**FULLY DIAGNOSED. One blocking site. One measured candidate (J2).**

### 1.1 The statement (difflib + co_lines evidence)
Official tuple landed: `[304, 302, 2, 40]`. The two jump-target hunks in
`logs/align_trade_op.txt`:

```
HUNK replace  orig[108:109]@676      ORIG  676 POP_JUMP_FORWARD_IF_FALSE  to 1000
                                     DECOMP 676 POP_JUMP_FORWARD_IF_FALSE to 1042
```

Block 1000 is one original statement, `write_info.append(items)` (original
`./fly_docker_py311/IQCommon/util/trade_info_utils.py` line 324, `co_lines` entry
`(1000, 8, 324)`), i.e. the unconditional tail of the `for` body that follows
`if items[0] in trade_id_list:`. In the landed product that line is emitted at 24
spaces of indent (inside the `else:` arm of `if operation == 'delete':`) instead of 20
(`for`-body level). Verified by specimen check:
`build_landed/IQCommon__util__trade_info_utils_OK.py` vs
`build_j2/IQCommon__util__trade_info_utils_OK.py` differ by exactly that one line,
which moves from 24 to 20 spaces; `return True` (original line 326) is untouched.
Because the statement is relocated rather than duplicated, the outer `if`'s FALSE edge
is re-targeted from 1000 to the loop-bottom 1042 — that is the jumpdiff hunk above.

### 1.2 The ONE blocking site
`core/cfg/region_analyzer.py`, `_collect_branch_blocks`, **line 26569**:

```python
if len(collected) > 1 and not merge:          # <-- W14-C reverse prune, gated on `not merge`
```

and its sibling `26632` (R37 reachability convergence) carry the same `not merge` gate, so
for *any* region whose merge is a real block the join-block prune never runs.

Probe evidence that this is the failing conjunct (`logs/probe_cbb2_tradeop.txt`, real file,
landed bytes):

```
CALLS:  entry=874 merge=654 stop=[654, 738, 1044, 1310, 1442, 1526]
                              -> [874, 886, 896, 908, 918, 1000]
FINAL:  IfRegion@726 cond=726 then_blocks=[738]
        else_blocks=[874, 886, 896, 908, 918, 1000]  merge=654 exit=654
```

i.e. the else arm of the *nested* `if operation == 'delete':` region owns 1000, the join
block of the *enclosing* `if items[0] in trade_id_list:` region
(`IfRegion@656 … merge=1000`).  Block 1000 has exactly two predecessors:
`918` (internal, fall-through inside the else chain) and `656` — and 656 is neither in
`collected` nor in `stop`; it reaches 1000 with `POP_JUMP_FORWARD_IF_FALSE` (its
fall-through successor is 678). That is precisely the W14-C external-jump-predator shape,
which is only pruned when `merge` is falsy. The secondary exemption consulted inside the
prune (`_w14_pred_is_child_structural_exit`, loose disjunct at **26670-26671**,
`any(b in in_set for b in rblocks)`) is *not* what keeps 1000: the conjunct `not merge`
short-circuits before it is ever reached. Both conjuncts therefore have to be addressed
together, and only the `merge is not None` side is new relative to R50/W14-C.

Cascade note (per the brief's warning about `merge is None` anchors): this candidate does
NOT touch a `merge = else_succ` site; it only *adds* a prune for `merge is not None` calls,
so it cannot re-home a refused claim. Measured: 0 REGRESSIONs on 4 files + 11 shapes.

### 1.3 Candidates, measured (≤2)
* **J1 — REJECTED** (`specs/cand_r64d3_j1.json.rejected`). W14-C analogue with a strict
  child-structure exemption (`region.entry in in_set`). Measured on my 4 files:
  `trade_operation` `[304,302,2,40] → [304,283,2,69]` — a 21-line loss; `probe_diffarms.py`
  localised it to calls `entry=414 merge=1468` and `entry=1082 merge=1360`, which drop
  `[1332, 1334, 1356]`: predecessor 1326 → 1332 is a *fall-through* edge of the
  `with`-cleanup path, my exemption demanded `WithRegion@414.entry ∈ in_set` (false), so the
  block was pruned and `return True` escaped out of `if len(write_info) > 0:`.
  Spec kept with `.rejected` + reason.
* **J2 — SHIPPING CANDIDATE** (`specs/cand_r64d3_j2.json`, single edit, anchor
  `# [R37 可达性收敛（W37）] 剪枝收敛后，仅保留从 entry 出发、沿正常` verified to occur
  exactly once; mirror build reported `1 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF`).
  Adds to `_collect_branch_blocks` a `merge is not None` twin of the W14-C reverse prune:
  fixpoint over `collected`; a block is dropped only if (a) it is not `entry`, (b) it has an
  external predecessor, (c) that predecessor reaches it by a **jump** edge (its fall-through
  successor, computed as the minimum-offset successor above `pred.end_offset`, is a different
  block), (d) that predecessor is neither in `collected` nor in `stop`, and (e) the block is
  not a `return None` tail (R14b/R37 none-tail exemption preserved). No region-ownership
  test, no `region.entry` requirement — the exact mistake J1 made.
  Measured (`FACTS.md` §5): `trade_operation` `[304,302,2,40] → [304,302,1,40]`
  (jumpdiff halved; the fixed hunk is exactly the @676 one from §1.1),
  `get_tick_direction` jumpdiff 3→1, `one_prod_to_ndarray` truediff 424→421,
  `get_real_minute_kline` truediff 197→194; `ab` tally
  **SAME=2 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0**; strict ruler **142/159 → 142/159**
  (unchanged, reported because the official ruler is blind here — both rulers given per
  the brief); shape battery **10 SAME / 1 MOVED / 0 REGRESSION**, still 4/11 clean.
  Honest read: J2 is *official-neutral on matched-function count* and strictly non-negative;
  it is a correctness fix on one pinned defect plus three incidental improvements, not a
  score mover. If the center only ships score movers, J2 is a documentation-grade fix.

### 1.4 Pinned-shape check for J2
`dump/shapes_landed.jsonl` vs `dump/shapes_j2.jsonl`, per file:
r63_ft 1/2 SAME · r63_ft2 1/2 SAME · r63_ft4 1/2 SAME · probe_r63b2_cases 6/9 SAME ·
probe_r63b2_cases2 3/9 SAME · repro_r63b2_tail_cmp_return 1/2 SAME ·
r63b3_chained_value_ctx_prefix 2/2 SAME · r63b4_tern_in_elif_chain 3/3 SAME ·
r63b5_w1 1/2 → **MOVED** (product bytes changed, matched count unchanged) ·
r63b3_chainstore_prefix 2/2 SAME · r63b4_cond_boolop_stmt_steal 13/13 SAME.

### 1.5 Residual hunk in the same function — family F2, NOT region ownership
```
HUNK replace  orig[59:60]@412    ORIG  412 POP_JUMP_FORWARD_IF_FALSE to 1468
                                  DECOMP 412 POP_JUMP_FORWARD_IF_FALSE to 1464
HUNK delete   orig[296:298]@1464  ORIG 1464 LOAD_CONST None / 1466 RETURN_VALUE
```
The original has a second, dead implicit `LOAD_CONST None; RETURN_VALUE` epilogue on the
`with`-cleanup exit path (block 1464/1466, reached only through cleanup block 1458); the
product collapses the two exit paths onto one epilogue. This is the per-exit-path exception
epilogue family (F2) — R61/R62 suppression attempts across 12 files falsified it as a
region-ownership problem; classification only, no candidate proposed (per the brief's F1/F2
instruction). Both J1 and J2 leave this hunk untouched, as expected.

---

## §2 D2/D3 — `order_api :: future_order` `[101,92,2,36]` and `option_order` `[83,73,3,39]`
**Diagnosed to the expression-emission layer; classified NOT region ownership; J2 inert.**

`logs/align_future_order.txt`, the two decisive hunks:

```
HUNK replace orig[71:80]@412   ORIG: 412 POP_JUMP_FORWARD_IF_TRUE to 676
                                      414 LOAD_GLOBAL NULL + strategy_log … 436 LOAD_CONST
                                      '生成订单，订单号：{order_id}，合约代码：{symbol}，方向：{side}{oper}，数量：{share}手'
                                      438 LOAD_METHOD format …
                                DECOMP: 412 POP_JUMP_FORWARD_IF_TRUE to 482     (9 insns gone)
HUNK delete  orig[104:109]@632 ORIG: 632 LOAD_FAST order_ / 634 LOAD_ATTR amount
                                     644 KW_NAMES / 646 PRECALL / 650 CALL
HUNK replace orig[88:92]@550   ORIG: 550 POP_JUMP_FORWARD_IF_FALSE to 556 / 552 LOAD_CONST '买入'
                                     554 JUMP_FORWARD to 558 / 556 LOAD_CONST '卖出'
                                DECOMP: …480 POP_JUMP…to 484 / 482 JUMP_FORWARD to 486 /
                                     486 LOAD_FAST order_ .futures_direction.value.upper()
```

So the whole `strategy_log.info('…'.format(**kwargs))` statement is consumed, the `{oper}`
ternary (`'买入' if … else '卖出'`) loses its constant arms, and the `{share}` kwarg slot's
`LOAD_FAST order_.amount / KW_NAMES / PRECALL / CALL` quintet disappears.

Region evidence (`logs/reg_future_order.txt`, `probe_own.py`): `IfRegion@340` and
`TernaryRegion@414`, `TernaryRegion@558` all carry `inline_boolop_chains` with
`'op':'or'`, and the ternary **condition** blocks 552/556 are absorbed into the enclosing
`IfRegion@192`'s `else_blocks` *before* the kwarg builder can own them.

**The requested difference from the R50 measurement** (banked lead: "if your diagnosis ends
back at a kwarg-slot bail, prove the difference from R50"): R50 characterised the bail
*inside* `_try_build_ternary_kwarg_call` (a kwarg slot whose value region is not yet an
expression → bail) plus a forward-only chain walk. The R64 evidence is *upstream of* that
bail: the slot never reaches the builder, because region ownership has already moved blocks
552/556 (and 632-650) into the enclosing if's `else_blocks`. Instruction-level proof: the
missing bytes are the `KW_NAMES`-terminated call sequence at 644-650 whose *preceding*
condition block 550 is claimed by another region (`IfRegion@340`, merge=…); R50's bail would
leave the block claim intact and only lose the call node. Consequence: a kwarg-slot patch
cannot fix this; it needs either the ternary-chain ownership rule or the log-statement
matcher — i.e. it is the F1-family "statement consumed by an enclosing expression emission"
shape, not a merge/ownership bail. No region-level guard proposed (brief rule). J2 leaves
`order_api` byte-identical (SAME).

`base_order` strict-only `[target_diff] #136 POP_JUMP_IF_TRUE` and the two official defects
share this `.format(**kwargs)` site family.

---

## §3 D4 — `risk_calculation :: _on_publish_after_trading_end` `[486,481,3,33]`
**Loop-body drop at the emission layer; NOT region ownership. Classified, no candidate.**

`logs/align_on_publish.txt`:

```
HUNK replace orig[490:499]@2762  ORIG: 2762 POP_JUMP_FORWARD_IF_FALSE to 2766
                                       2764 JUMP_FORWARD to 2808
                                       2766 LOAD_GLOBAL NULL + time / 2778 LOAD_ATTR sleep
                                       2788 LOAD_CONST 0.01 / 2790 PRECALL / 2794 CALL
                                       2804 POP_TOP / 2806 JUMP_BACKWARD to 2748
                                 DECOMP: 2760 POP_JUMP_FORWARD_IF_FALSE to 2764 / 2762 NOP
HUNK replace orig[481:483]@2744  ORIG: 2744 POP_JUMP…to 2808 + 2746 NOP
                                 DECOMP: 2744 POP_JUMP…to 2764
```

Nine original instructions — the entire `time.sleep(0.01)` body plus the loop back edge —
collapse to two NOPs. But region ownership is *correct*: `logs/reg_onpub.txt` shows
`LoopRegion@2748 blocks=[2746, 2748, 2764, 2766]`, i.e. the loop region exists, contains its
body block 2766 and its back edge, yet the generator emits the region straight-line, drops
the body statement and turns `break` into `pass`. That is a
region-AST-generator rendering defect (loop-region with a `NOP`-headed condition block),
outside the region-reduction layer I own; a `_collect_branch_blocks` change cannot reach it,
and the 11-shape battery contains no analogous pinned shape. Also carries an F1 mangled
f-string hunk at `orig[230:231]@1352` (lambda code-object line 343 → product line 220).

## §4 D5 — `risk_calculation :: _save_testds_to_csv` `[71,68,7,19]`
**Statement/block fusing at the emission layer; NOT region ownership. Classified.**

`logs/align_save_testds.txt` shows three independent original-statement failures:
1. `HUNK delete orig[60:62]@280` — `IMPORT_NAME IQEngine.plugins.plugin_system_risk_calculation.function`
   + `IMPORT_FROM THREAD_STATUS` consumed: the product emits
   `THREAD_STATUS = ('THREAD_STATUS',)` (an F1-class mangling) although the *identical*
   import renders correctly at product line 253 elsewhere in the same file — so it is not a
   name-resolution limit but a per-statement emission issue.
2. `HUNK replace orig[65:68]@290` — `292 LOAD_CONST None / 294 RETURN_VALUE` (original bare
   `return`) replaced by `286 JUMP_FORWARD to 342`, i.e. `return` degraded to `break` inside
   the loop that the previous hunk created.
3. `HUNK insert … 108 NOP` + `POP_JUMP_BACKWARD_IF_FALSE to 122/124` — a spurious
   `while True:` wrapper around statements the original had at straight-line level.
All three are in `region_ast_generator.py` (statement fusion / loop synthesis), not in
region ownership. J2 leaves this file byte-identical (SAME).

---

## §5 Not diagnosed this round (recorded so the next shift does not re-spend on them)
* `real_quote` — 5 defects, all `truediff ≥ 100` (`get_cache_l2_data` [337,335,2,313],
  `get_cache_l2_data_by_one` [321,320,2,300], `get_real_minute_kline` [253,254,3,197],
  `get_tick_direction` [259,258,3,102], `one_prod_to_ndarray` [605,607,5,424]). Huge
  truediff with near-zero jumpdiff is the mangled-f-string/logging (F1) signature. J2 moves
  two of them incidentally (see §1.3) but matched count stays 39/44.
* `trade_info_utils :: get_trade_list` [339,323,14,148] — 14 jump diffs, i.e. a genuinely
  different control-flow reconstruction; needs the same region-ownership work as D1 but is
  *not* touched by J2 (`probe_cbb2` on this function was not run this round).
* `risk_calculation :: get_TradeMode_trades` [1839,1753,4,1620] — 86 missing instructions,
  largest single loss on my targets; unexamined this round.
* `_on_set_positions` [seq_len] 297→298 (strict-only extra) — unexamined.

## §6 Repro engineering — negative result (see NONE.md §N3)
`test_repros/round64_diag3/r64d3_postif_join.py` (+ `.pyc`, py3.11) reproduces D1's *region
over-claim* exactly but not D1's *product* defect. v1-v3 failed because the join block became
the loop's `back_edge_block`; v4/v5 carry the over-claim into the region forest and still
emit correct product code. The one genuinely new fact bought at high cost: the join block must not be
the `LoopRegion.back_edge_block`, because `region_analyzer.py:18291`
(`else_blocks = [b for b in else_blocks if b in _loop_body_only or b is _r57d_keep_be or
self._block_exits_loop(...)]`) prunes the back-edge block first; back-edge selection is
`max()` over `(no exc-epilogue ops, #non-jump instructions, start_offset)` at
`region_analyzer.py:4088-4095` — real: `738 → (1,22,738)` beats join `1000 → (1,6,1000)`;
v3 repro tied at `(1,6,·)` and the join block won the offset tiebreak. v5 adds three-level
nesting (isomorphic forest) on top of that precondition and still yields 2/2 clean on landed. Therefore D1's product symptom needs an
ingredient in `region_ast_generator.py` that the region forest alone does not determine;
per the brief I record the failure instead of faking a repro.
