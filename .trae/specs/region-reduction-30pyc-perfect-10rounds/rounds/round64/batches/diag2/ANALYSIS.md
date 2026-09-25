# ANALYSIS — Round 64 · batch diag2

Read `FACTS.md` first for numbers/provenance. Line numbers below are **landed** lines of
`core/cfg/region_ast_generator.py` as checked out in the worktree (bare-LF copy; numbering identical
to the landed CRLF copy because only CRs differ — see FACTS §0).

---

## D1 — `IQEngine/utils/scheduler.pyc :: Scheduler.run_interval_trade.is_run_interval_time_now`
landed [225, 201, 2, 173] → **c1 / c12 = cleared, 43/45 for the file**

**Missing original statement(s)** (`logs/align_isrin.txt`, `logs/trace_isrin.txt`):
the whole `return (RI_STOCK_AM_OPEN < current_time < RI_STOCK_AM_CLOSE or
RI_STOCK_PM_OPEN < current_time < RI_STOCK_PM_CLOSE)` at original **L394** =
`delete orig[68:92] n=24 @410..@512`. Blocks (`logs/reg_isrin.txt`):
`B@410 LOAD_GLOBAL LOAD_FAST SWAP COPY COMPARE_OP JUMP_IF_FALSE_OR_POP → succs[436,456]`,
`B@436 LOAD_GLOBAL COMPARE_OP JUMP_FORWARD → 460`, `B@456 SWAP POP_TOP → 460`,
`B@460 JUMP_IF_TRUE_OR_POP → succs[512,462]` (the `or`), `B@462/488/508` = the second chain,
`B@512 RETURN_VALUE`. Two adjacent `replace` hunks (`@270 JUMP_FORWARD` → `LOAD_CONST None;
RETURN_VALUE`, `@400` same) are the *consequence*: the elif arm is truncated to `return None`.

**ONE blocking site**: `_process_if_blocks`, landed **L21147-21149**
```
for _nb in _nr.blocks:
    self.generated_blocks.add(_nb)
    self.generated_offsets.add(_nb.start_offset)
```
Failing conjunct downstream: **L21098 `if block in self.generated_blocks: continue`**, which stands
between that over-claim and the dispatch that would have emitted the statement,
**L21192 `if block in child_expr_regions:`** (`child_entries`/`child_expr_regions` built at
L20876-20888 from `region.children`, BoolOp/Ternary entries only).

**Mechanism chain** (`logs/path_410.txt`, `logs/path_410_if.txt` — statement-level path trace):
elif arm blocks `[202,204,270,410,436,456,460,462,488,508,512]` → scan reaches 410, which is in
`_nested_if_entry_generate` (L21134) → `_generate_region(IfRegion@410)` → inside `_generate_if` the
R36 value-context chain-compare contract fires: L11502-11527 builds the chain, caches it as
`self._chain_compare_expr_cache[id(_merge)] = _cc_expr`, `self._generated_regions.add(id(region))`
and **`return []`** (its own comment: "Don't mark blocks as generated — the BoolOpRegion will handle
them"). Back in the parent, `_nr_ast` is empty and L21147 nevertheless claims **460** — which is the
*entry of the sibling BoolOpRegion@460* (a direct child of `IfRegion@0`, i.e. `460 in child_entries`)
— so when the address-ordered scan reaches 460 the L21098 continue fires first and the
`child_expr_regions` consumer is never dispatched ⇒ the 24-instruction `return` disappears.
Same for `IfRegion@462`, whose merge is also 512/460-side.

**Candidate**: `specs/cand_r64b2_chaincompare_yield.json` (arm `c1`, +33 lines at that loop).
**Measured**: scheduler 42→43, wizard/klinedata/api_base product shas byte-identical to landed
(no regression), battery 34/48 → **40/48** with `REGRESSION=0 MOVED=0` (FACTS §2, §3).
**Verdict: fixed it.**

### Rule as it must be stated (three elements, pure structural predicates)
*Recognition condition* — three facts, all visible at the level that owns the loop:
(1) the nested region just reduced emitted **nothing** (`not _nr_ast`);
(2) the block under claim is the **entry of a sibling child region of this same level**
(`_nb in child_entries`, where `child_entries` = `{child.entry for child in region.children}`);
(3) it is not the yielding region's own entry (`_nb is not _nr.entry`).
*Reduction* — the yielding region keeps claiming its own interior blocks (otherwise the chain links
`B@436/B@456/B@488/B@508` re-enter the scan as plain blocks and leak bare expressions) and abstains
from claiming the sibling entry, so the block-order dispatch hands it to the real consumer region;
when nothing yields, behaviour is byte-identical to landed.
*AST mapping* — the cached `Compare`/`BoolOp` expression becomes the value of the enclosing arm's
`Return` node (`IfRegion.orelse[-1].body[-1].value = BoolOp(Or, [Compare(a<t), Compare(t<b), …])`),
the parent referencing the child region through its entry block only (principle 4).

### Forbidden-shape audit
* No cross-region / cross-level containment: no `region.entry in r.blocks`, no `for r in self.regions`
  scan, no `block_to_region` lookup. `child_entries` is a **same-level** entry set built 270 lines
  above in the same call frame. (Contrast: landed L21205-21208 does carry such a scan — untouched here.)
* No opname list in the predicate; nothing keyed on function names, offsets or thresholds.
* `self.*` usage is limited to the pre-existing emit-mark sets (`self.generated_blocks`,
  `self.generated_offsets`) and `self._generated_regions` — no new frame state.
* Honest over-breadth note: (1) uses "emitted nothing" as a proxy for "yielded by contract". Any other
  empty reduction also stops claiming sibling entries. Corpus evidence for that being harmless in this
  batch: 0 regressions across 4 targets + 15 battery files, and 6 *additional* battery functions fixed.

### Attempts / falsified variants (from the surviving logs)
* **Falsified — "the chain expression is never built"**: `path_410_if.txt` shows `_generate_if` reaching
  L11519 → L11523 (`self._chain_compare_expr_cache[id(_merge)] = _cc_expr`) before `return []` at L11527,
  so the expression exists and is cached; the loss is entirely downstream. A cache-side fix would be inert.
* **Falsified — "let the yielding region claim nothing at all"** (i.e. `if not _nr_ast: break` before the
  claim loop): ruled out by the same block dump — `B@436/B@456/B@488/B@508` would then be re-entered as
  ordinary blocks. (This is what `_nb is not _nr.entry` alone would do; condition (2) is what discriminates.)
* `logs/path_ghf_block.txt` is **empty** — the block-level probe for the api_base case produced no hits
  (dead end, kept for the record). No other candidate variants are documented by the previous agent for
  this defect.

---

## D2 — `IQData/api/api_base.pyc :: get_future_history_df`
landed [973, 957, 3, 229] → **c2 / c12 = cleared, 24/25 for the file**

**Missing original statement(s)** (`logs/align_ghf.txt`): `delete orig[800:817] n=17 @4274..@4360`,
original **L298-L299** = `count_c = len(_1m_df_nan_data[(_1m_df_nan_data['datetime'] >= _query_date)
& (_1m_df_nan_data['datetime'] > left)])`. Downstream evidence of the hole: at L304 the product reads
`LOAD_GLOBAL:'count_c'` where the original reads `LOAD_FAST:'count_c'` (`replace orig[837:838]
decomp[820:821]`) — the consumer variable became a dangling global, i.e. the assignment was never emitted.

**ONE blocking site**: `_if_extract_cond_instructions` (def landed **L13975**), the R09 clear guard at
landed **L14360-14363**
```
if (not _has_format_value and not _next_is_format_value
        and not _next_consumes_as_subexpr
        and not _next_is_assign_store):
    pre_instrs = []
```
with `COMPARE_OP` hit at `cond_block B@4020` instruction @4304 (`>=`). Failing conjuncts, in order:
`_next_consumes_as_subexpr` (L14334-14339) only inspects the **immediately next** instruction, which is
`LOAD_FAST:'_1m_df_nan_data'` → False; `_next_is_assign_store` (L14348-14359) skips LOAD\*/stack noise and
**breaks at `BINARY_SUBSCR`** (@4336) without entering any exemption → False; the two f-string conjuncts
are False. So the guard clears the accumulated `LOAD_GLOBAL len / LOAD_FAST _1m_df_nan_data / …` prefix,
the later `STORE_FAST count_c` can no longer reconstruct a statement, and the assignment is dropped.

**Mechanism chain**: block @4274-@4360 mixes *statements* (`left = …`, the `len(df[mask])` assignment)
with the region's condition tail; the "first COMPARE_OP after the last store" heuristic assumes the
compare's consumer is adjacent. In pandas-style mask arithmetic the consumer (`BINARY_SUBSCR` of the
`&`-combined mask) sits 6 instructions later, so the assumption fails and a **value-context** compare is
misclassified as a **branch-context** (if-condition) compare.

**Candidate**: `specs/cand_r64b2_condcomp_consumer.json` (arm `c2`, +42 lines, inserted between the
`_next_is_assign_store` scan and the clear guard). **Measured**: api_base 23→24, scheduler sha == landed
sha (inert there), wizard/klinedata identical, battery unchanged at 34/48 (all shas equal to landed,
`dump/c2f_shapes.jsonl`) ⇒ c2 is *narrow*: it fixed exactly one function on this batch's corpus and is
otherwise neutral. **Verdict: fixed it.**

### Rule as it must be stated
*Recognition condition* — treat the COMPARE_OP's result as value-stack depth 1 and simulate the rest of
the block forward with `dis.stack_effect` (via the landed pure helper `_instruction_stack_effect`,
L426-441), skipping `RESUME/NOP/CACHE/EXTENDED_ARG`; the **first instruction that returns the depth to
zero is the consumer of this comparison**. Consumer ∈ branch family ⇒ the compare feeds a control-flow
edge ⇒ keep landed behaviour; consumer ∈ value family ⇒ the compare is a sub-expression of a statement
that has not terminated yet. Stack effect unavailable or depth underflow ⇒ tri-state stays `None` ⇒
landed behaviour (fail-safe).
*Reduction* — the clear `pre_instrs = []` is guarded additionally by
`_cond_consumer_is_branch is not False`: in value context the accumulated prefix is **kept** and later
terminated by the following `STORE_*` into an `Assign`. The new clause can only *prevent* a clear, never
cause one, so it is monotone-safe against every landed behaviour that keeps the condition.
*AST mapping* — value context ⇒ the `Compare` becomes a child of the subsequent statement's value
(`Assign(count_c, Call(len, [Subscript(df, BinOp(BitOr/BitAnd, Compare, Compare))]))`, parent references
the sub-expression, principle 4); branch context ⇒ the `Compare` enters `IfRegion.test` as before.

### Forbidden-shape audit
* No cross-region / cross-level containment, no offsets, no function names, no thresholds; the scan is
  confined to `_iter_instrs` of the one block being analysed (`_instr_idx` is the loop index of L14063).
* `self.*` is used only to call a landed `@staticmethod` pure function ⇒ no frame state.
* ⚠ **Opname-list predicate** — the branch family is spelled as
  `CONDITIONAL_JUMP_OPS / SHORT_CIRCUIT_JUMP_OPS / NONE_CHECK_OPS / 'POP_TOP'`. Two caveats the center
  should price in: (a) `POP_TOP` as "branch" is a judgement call (a popped compare is a bare expression
  statement, and treating it as branch reproduces landed behaviour, so it is conservative but not
  derived from the stack model); (b) the value family is *implicit* ("anything that zeroes the depth and
  is not in the branch list"), so a future 3.12+ opcode list would need re-audit. The opname lists are the
  only non-structural part of this rule; the *predicate* itself (stack discipline) is structural.
* ⚠ **Under-specified generality** — c2 is measured on exactly one real function plus one synthetic.
  Its blast radius on the other 398 files is unmeasured in this batch (see recommended choice).

### Attempts / falsified variants
* **Falsified — "widen the adjacency window"** (landed's own `_next_is_assign_store`, R09 + W15-E): it
  already skips noise and LOAD\* and stops at the first non-LOAD — measured behaviour *is* the bug
  (`break` at `BINARY_SUBSCR` @4336), so no window widening of that shape can fire; the discriminator has
  to be stack depth, not instruction class.
* **Falsified — block-level hypothesis for B@4020**: `logs/path_ghf_block.txt` is empty (the probe on the
  block/region level recorded no evidence), the decisive site is instruction-local inside
  `_if_extract_cond_instructions`; `logs/reg_ghf.txt` confirms `B@4020 succs=[4538,4596]` is a mixed
  statements+condition block, which is why a per-instruction rule is required.
* **Not attempted / open**: whether the same stack-consumer judgement should also replace the `_next_*`
  conjuncts wholesale (rather than being added as a 5th guard). Left as-is deliberately — the additive
  form is what was measured.

---

## D3 — `IQData/api/api_base.pyc :: get_history_df` — landed & c12 [1742, 1719, 14, 1277]
`logs/r64_dalign_ghd.txt` (fresh: `python -X utf8 dalign.py …api_base.pyc
build_landed/IQData__api__api_baseOK.py get_history_df`, 10 hunks, −25 net, 39 lost / 14 gained).
Dominant loss: `delete orig[1025:1048] n=23 @4986..@5100` = original **L522-L524**
`tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)` followed by
`if tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0:` — the product
jumps from `if fq == … and len_real_data > 0: return …` straight to L377 (`LOAD_FAST fields`), so a whole
guarded statement run behind a short-circuit `and` chain vanished. Second family present:
**condition-polarity/arm swap** — 4 hunks where original emits
`POP_JUMP_FORWARD_IF_TRUE` + body + `JUMP_FORWARD` and the product emits `POP_JUMP_FORWARD_IF_FALSE` with
the arms exchanged, dragging `time_count -= 1` / `max_len_real_data -= 1` past the condition
(`jumpdiff` 14 comes from here), plus 2 duplicated 4-instruction `insert` hunks.
**Not** c2's family: c2 leaves this function's tuple byte-identical ([1742,1719,14,1277] on both arms),
i.e. no value-context COMPARE_OP clearing occurs on its path. → **only found it**; it is the reason
api_base stops at 24/25 (see Job 5).

## D4 — `IQEngine/utils/scheduler.pyc :: Scheduler.get_checked_time` — [106, 106, 0, 43]
`logs/r64_dalign` style evidence: `delete orig[23:31] n=8 @130..@166 (src L241)` + `insert decomp[63:71]
n=8 @352..@388 (src L156)` ⇒ equal counts, zero jump diff: `hour, minute = divmod(minute_time, 100)` is
emitted **after** the `PUSH_EXC_INFO/…/RERAISE` epilogue instead of before the try-tail `JUMP_FORWARD`.
This is the known **per-exit-path exception-epilogue** family (statement misplaced across the handler
boundary), *not* a region-ownership problem. → **only found it**. No region-level guard should be tried.

## D5 — `IQEngine/utils/scheduler.pyc :: run_daily` — [77, 71, 0, 56] (unverified naming caveat)
Official tuple shows 6 instructions lost with `jumpdiff=0`. The non-invasive aligner reports
`orig=12 decomp=12 hunks=0` for the code object it picks by name ⇒ there are **two code objects named
`run_daily`** (module function + a nested one) and `dalign.py`'s name picker resolves to the wrong one;
`logs/sum_scheduler.txt` carries the same misleading `run_daily 12/12` line. Not diagnosed further.
→ **only found it**, with a measurement caveat to hand over.

## D6 — `IQCommon/strategy/wizard_quant_api.pyc :: params_analysis` — [133, 126, 1, 117]
`logs/trace_params.txt` + `logs/reg_params.txt`: the first arm's
`try: value = value[-1] / except BaseException: value = value` reduces, then
`delete orig[20:29] n=9 @48..@84 (src L151)` = `B@48 = LOAD_FAST LOAD_FAST LOAD_GLOBAL LOAD_FAST
PRECALL CALL LOAD_CONST BUILD_CONST_KEY_MAP RETURN_VALUE` — the whole `return {…}` dictionary of the
`up_v/down_v` arm is gone; the product instead falls into `elif filter_type == 'region_v'`, and the two
`replace n=2` hunks at L147/L149 show the arm-swap/polarity shape of D3 again.
→ **only found it** (same polarity/arm-swap + swallowed tail family, not a same-level ownership bug).

## D7 — `IQCommon/strategy/wizard_quant_api.pyc :: get_DMI.calculate_di` — [75, 73, 0, 45]
`orig[38:41]` `LOAD_CLOSURE high, LOAD_CLOSURE low, BUILD_TUPLE:2` → product
`LOAD_CLOSURE high, BUILD_TUPLE:1`, and `orig[56:57]` drops a `LOAD_CLOSURE:'low'` before `sum(...)`:
a **generator-expression closure free-variable tuple** built with wrong arity (nested genexpr code
object, `MAKE_FUNCTION:8`). Part of the first hunk is only the `<code object …>` repr differing by file
path, which `bytecode_diff` counts as a true-diff — a metric artifact worth remembering, not a defect.
→ **only found it**; neither of the two known families nor a region-ownership case.

## D8 — `IQCommon/api/klinedata.pyc` (3 functions)
* `get_all_real_daily_kline` [188,187,3,26]: `delete orig[182:183] n=1 @900` + one 1-instruction replace
  at @580 ⇒ single lost instruction with 3 jump diffs — a small arm/polarity case (D3 family).
* `get_multiminute_his_data` [479,478,3,16]: two `replace n=2/n=1` hunks at @2708/@2758 — same shape.
* `kline_datetime_list` [389,389,9,228]: equal counts, 4 hunks, two `insert n=4` (`EXTRA
  decomp[331:335] @1380..1386 src=L922`, `decomp[404:408] @1702..1710 src=L933`) against two
  `replace n=5` ⇒ duplicated 4-instruction emission of an `or`/ternary tail plus a compare-chain
  re-polarity; this is the **mangled/duplicated emission** family.
→ **only found them.**

---

## Family assignment for the still-open defects (Job 3 closing requirement)
| defect | tuple | family | same-level region guard appropriate? |
|---|---|---|---|
| `get_checked_time` (D4) | [106,106,0,43] | per-exit-path exception epilogue (statement across the handler boundary) | **No** |
| `run_daily` (D5) | [77,71,0,56] | unassigned (aligner name collision; not diagnosed) | unknown |
| `get_history_df` (D3) | [1742,1719,14,1277] | condition-polarity/arm swap + swallowed guarded statement run; 2 duplicated inserts (mangled/duplicated emission) | **No** (polarity/arm-swap is `_generate_if`/merge-block territory) |
| `params_analysis` (D6) | [133,126,1,117] | swallowed arm tail (`return {…}`) + arm swap | **No** |
| `calculate_di` (D7) | [75,73,0,45] | genexpr closure `BUILD_TUPLE` arity (+ partly a repr artifact) | **No** |
| `get_all_real_daily_kline`, `get_multiminute_his_data` (D8) | jd 3 | condition-polarity/arm swap | **No** |
| `kline_datetime_list` (D8) | [389,389,9,228] | mangled/**duplicated** emission | **No** |

None of the eight remaining defect tuples is a same-level region-ownership case like D1/D2; proposing
further `child_entries`-style guards for them would be off-target.
