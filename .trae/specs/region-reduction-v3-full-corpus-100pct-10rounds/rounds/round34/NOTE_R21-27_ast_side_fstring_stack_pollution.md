# NOTE_R21-27 (round 34 → for round 35) — the f-string glue is AST-side stack pollution, and two claims in the old ticket are false

Measured 2026-10-11 17:40-17:43 on the **gate-34 sealed base** (generator `065e4d77243190dc`, analyzer
`35e227ac3e7b25af`, repo untouched — all probing ran in-process against the installed sources).

Victim: `trade_live_broker.pyc :: etf_purchase_redemption`, shape re-measured this round
`len orig=426 prod=414 delta=-12 / 5 hunks / 0 landings, judge_diff=True`.

## 0. What `rounds/round32/TICKET_R21-27_...md` got wrong (corrected by measurement, not opinion)

1. **"the defect is upstream of `code_generator`"** — half true, but the conclusion it was used to justify
   (stay out of the renderer files) rests on a misreading: the corruption is visible in the **AST dict**, not
   only in the emitted text, and `code_generator._generate_joined_str_from_dict` behaves correctly given the
   node it is handed (§2).
2. **Root-site list at `:50309` / `:50869` / `:50490`** — stale line numbers on this base (`
   _fstring_parts_from_segment` is now `:50536`) and, more importantly, that segment reducer is **guarded**:
   it returns `None` unless the stack bottom is all string `Constant`s, so it cannot be the source of raw
   `Name` parts.
3. The residual register describes this unit as `属性链截断` (attribute-chain truncation). The measured cause
   is different: a **stack drain** that leaves the surrounding statements' leftovers inside the f-string.

Also on the record: my own first reading of the scan output said "the AST is clean". That was an artifact of
`tail` truncating the scan; the full scan (48 clean nodes, 1 suspicious) contradicts it. Registered here so
the next session does not inherit my truncated conclusion.

## 1. The AST node, as produced by the installed generator

Driver `D:/Temp/r35_joined.py` (walks the generated AST dict, prints every `JoinedStr`'s parts):

```
suspicious at  .../body[50]/body[0]/orelse[3]/orelse[1]/body[10]/orelse[7]/value
   ('Constant', '')
   ('Name',      ...)      <- raw Name node inside JoinedStr.values
   ('Constant', '0')
   ('Constant', '0')
   ('Name',      ...)
   ('Name',      ...)
```

`values` mixes bare `Name` nodes and non-string `Constant`s with the real literal parts. The original
statement is `strategy_log.info(_(f'生成订单，订单号：{order.order_id} 代码：{order.symbol} 数量：{...}{abs(amount)}'))`
followed by `return order.order_id` (BUILD_STRING 7 = 3 literals + 4 formatted values), and the emitted
product instead has one `return f"list_info00orderstrresultentrust_noselforderorderselfstrorderselforderselforderstrategy_log_生成订单，订单号：{order!s} …"`
— the leftover stack (`list_info`, the two `0` subscripts, `order`, `str`, `result`, `entrust_no`, `self`, …
and the two callees `strategy_log`, `_`) glued in front of the real literal, with the `Call` wrappers and the
`return order.order_id` gone. That single root explains all five hunks (the lost `PRECALL/CALL` pairs and the
lost `LOAD_FAST/LOAD_ATTR` are the *same* absorption, not separate defects).

## 2. Why the renderer is not the bug

`code_generator._generate_joined_str_from_dict` (:4659-4720 on this base) classifies each part:
`Constant` with a **str** value → literal text; `FormattedValue` → `{expr}`; anything else →
`_generate_expression(...)`. Given a `values` list that contains `Name` nodes and int `Constant`s, no
renderer can recover the intended f-string — the information (that those entries were *statements*, not
parts of this string) was already destroyed when they were pushed into `values`. So the fix belongs where
`values` is assembled, and the renderer needs no change.

## 3. Where to look, with the guard that must not be assumed guilty

`_fstring_parts_from_segment` (`region_ast_generator.py:50536`) refuses any segment whose stack bottom is
not all string constants, and returns `None` on underflow/exception — it cannot emit a raw `Name` part. The
polluted node is produced by the **caller** path: the `merge_ctx == 'fstring'` assembly at
`:51100-51236` (`_fstring_parts` ← ternary chain + intermediate-merge prefix scan + `_tail_parts`), whose
prefix scan appends `LOAD_CONST` operands as literals and whose fallback
(`:51221-51234`, `_after_fv` re-scan) appends every `LOAD_CONST` after the first `FORMAT_VALUE` until
`BUILD_STRING`. Duty for the fix: identify which of those appends contributes the `Name` entries — measure
by wrapping ONLY that assembly function and dumping `_fstring_parts` types per call, never by reading
`values` types back into the pipeline.

## 4. Probe hygiene notes from this session (measured, so the next one does not repeat them)

- Wrapping 86 builder methods (`D:/Temp/r35_who.py`) changed the generated source size
  (169307 vs 175258 chars) — that run is a **perturbing probe**; its numbers were not used for any claim.
- Wrapping 8 loop methods (`D:/Temp/r35_loopwho.py`) with a no-op wrapper and with a logging wrapper both
  produced 175258 chars → certified inert for this target, and it is the source of the "which path renders
  header @46" finding that falsified `TICKET_R21-33` §8.
- `D:/Temp/r35_attr_probe.py` (wrapping two pure builders) also certified inert: 175258 == 175258.
- Read-only CFG/analyzer censuses (`rounds/round34/census_r34_loop_tail.py`,
  `D:/Temp/r34/else_census.py`) do not generate products, so they cannot perturb them.

## 5. Acceptance bar for whoever takes this

`etf_purchase_redemption` → `delta=0 hunks=0 landings=0 judge_diff=False`, broker 123 → **124/128**;
report the other five broker units' shapes before/after (`_process_order -465/4/1`,
`_process_cancel_order -293/3/0`, `_sync_worker -3/5/6`, `_trade_status_handle -3/3/2`,
`ipo_stocks_order 0/0/0` — perturbing the landed one is a regression); census the predicate's population
over the verification face with named controls, then the 20-file panel, then the gate. Mirror `D:/Temp/r30chk`
is currently byte-identical to the landed base (generator `065e4d77243190dc`, analyzer `35e227ac3e7b25af`),
pristine copies at `D:/Temp/r33/backup_r30chk_generator_e7e2b2dd4cf6ed64.py`,
`D:/Temp/r34/pristine_fcf2b870f0fb71b3_region_ast_generator.py`,
`D:/Temp/r34/pristine_35e227ac3e7b25af_region_analyzer.py`.

## 6. The refusing segment is measured — the prefix window sweeps in preceding statements (17:47)

Wrapping `_fstring_parts_from_segment` to log its inputs (`D:/Temp/r35_seg.py`, whole-module generation of
`trade_live_broker.pyc`):

```
segment calls=2  refused(None)=1
   REFUSED seg @[1968]..@[2312] n=54 hasSTORE=True
   ok       seg @[2392]..@[2410] n=4  -> ['FormattedValue']
```

So the reducer is handed a **54-instruction window that contains `STORE_*` opcodes** — preceding statements
(`list_info = (result, '')`, `result = list_info[0][0]`, `order.set_entrust_no(...)`, `self.orders.append(...)`,
the two callee pushes `strategy_log` / `_`) — and it refuses, correctly: no f-string prefix segment contains
an assignment. The caller's fallback then fabricates **one part per `LOAD_*`**, which is precisely the glued
`list_info`, `0`, `0`, `order`, `str`, `result`, `entrust_no`, `self`, …, `strategy_log`, `_`.

**Fix shape (measured target):** bound the prefix window at the last statement boundary before the f-string's
own parts. The window is sliced at `region_ast_generator.py:45048-45051`
(`_prefix_instrs = cond_block_instrs[_r65_callee_skip:cond_val_start]`) and the same `_r65_callee_skip` bounds
the R66-d2 segment loop at `:45097-45103`, so advancing that skip past `STORE_*` / call-closing `POP_TOP` /
jumps fixes both the per-`LOAD_*` scan and the segmenter in one place. The chained path has its own twin
window at `:51120-51135`, so check whether the refusing call comes from `:45103` or `:51210` before editing —
the 54-instruction segment is the evidence to match, not the line numbers.

Honest caveat on these numbers: this wrapped run emitted 166370 chars while the unwrapped and the 2-method
wrapped runs emitted 175258, so **sizes from wrapped runs are not evidence** (probing inside the pipeline
perturbates, as already recorded in §4). The segment offsets/instruction-count/`STORE_*` presence are
structural readings of the arguments a method receives and stand on their own; re-verify against a clean run
before quoting any byte count.
