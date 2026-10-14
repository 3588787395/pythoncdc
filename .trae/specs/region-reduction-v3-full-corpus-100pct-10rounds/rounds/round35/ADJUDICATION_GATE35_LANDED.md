# Gate 35 adjudication and landing record

Landed file: `core/cfg/region_ast_generator.py` `pre=065e4d77243190dc` → **`87910190b7ef7c35`**
(3825793 bytes, BOM + all-CRLF preserved, 0 bare LF, `py_compile OK`). Four co-requisite hunks built by
`build_cand_r35_R21-27.py` → `build_cand_r35b_R21-27_chain.py` → `build_cand_r35c_R21-27_callee_skip.py` →
`build_cand_r35d_R21-27_part_kind_filter.py`, each anchor-asserted. One product moved on the panel
(`trade_live_brokerOK.py`); the gate moved exactly that one file's unit count.

## 1. Certified numbers (`gate_chain.py 35 34`, all four stages rc=0)

- regen `ok=402 bad=0` (187 s), verify (144 s)
- report: **units 6610 → 6611 /6617 (99.9093%), files 399 → 399**,
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`
  - FIXED `trade_live_broker.pyc <module>.TradeLiveBroker.etf_purchase_redemption` → **123 → 124/128**
- checks (100 s): quotation **153/153**, small34 `units_success 1562 / success 31` (+1, moved by exactly the
  flip count), ruler selfcheck OK (both mutation arms 1/153),
  pytest `2 failed, 282 passed, 2 xpassed` (the two registered residents)
- sealed residual: **3 files / 6 units**, `UNREGISTERED 行数=0` (`RESIDUAL_ROUND35.md`)

## 2. What was actually wrong (four causes, not one)

The unit was `-12 / 5 hunks / 0 landings`. Emitted text `return f"list_info00orderstrresultentrust_no…"`
looked like one f-string bug; measurement split it into four, and **none of them alone flipped the unit**:

1. the f-string prefix window `cond_block_instrs[_r65_callee_skip:cond_val_start]` swept in whole preceding
   statements — the segment reducer was handed a **54-instruction window containing `STORE_*`**
   (`@1968..@2312`, refused → `None`) and fell back to `fstring_parts = _stack`, fabricating one part per
   `LOAD_*`;
2. `_try_wrap_fstring_pending_call` accepts a **single** `(PRECALL|KW_NAMES)* → CALL(arg=1)` pair before
   `POP_TOP`, but `strategy_log.info(_(f'…'))` is the gettext idiom = **two** pairs, so `_rest[0]` was the
   second `PRECALL` and the screen returned `None` → the statement degraded to `return f'…'`, dropping both
   calls and the following `return order.order_id` (this is where the 12 instructions were);
3. `[R65-d3 C1a]` strips only the **first** pending callee group, so the second was still rendered into the
   literal (`strategy_log_`);
4. the fallback had pushed the ternary condition's own operand name (`LOAD_FAST order`, never consumed by a
   `FORMAT_VALUE`) into `JoinedStr.values`, where the renderer folds a non-`Constant`/non-`FormattedValue`
   part into the literal (`' 数量：order'` instead of `' 数量：'`).

Progression measured per hunk (`FIX_R21-27_r35.md` §3): −12/5 → (h1) **−12/5, text only** → (h2) −2/4 →
(h3) 0/1 → (h4) **0/0/0 Equal**. Hunk 1 is the cautionary one: it deleted every visible symptom of the glue
and moved **zero** instructions, because a shorter string constant is still one `LOAD_CONST`. It is kept as a
co-requisite, not presented as progress.

## 3. Population and controls

Census before editing (`D:/Temp/r35_chain_census.py`, whole verification face): **36** merge tails with one
call pair keep the existing `_r27_pairs == 1` path untouched, **3** have two pairs —
`etf_purchase_redemption`, `_process_order`, and `get_covered_amount`. The last is a **green** unit, so it was
re-measured explicitly: `delta=0 hunks=0 landings=0 judge_diff=False`, i.e. the extension does not disturb
it. The other panel files came back **byte-identical** (19 of 20 `SAME`), including quote 91/92,
real_quote 45/45, quotation 153/153, handlers 30/30 and all six duplicated-module canaries — this is the
check that rejected gate 31 attempt 1's mode and this round's own R21-28 v1, so it was run before the gate.

All four rules are opcode-class / stack-shape judgments over one block's own instruction stream (no function
names, no offsets, no counters, no cross-region containment), consistent with the spec's
correct-at-identification and unique-membership constraints.

## 4. Ticket claims corrected by measurement

`rounds/round32/TICKET_R21-27_…` said the corruption is upstream of `code_generator` and listed root sites
that had drifted; `NOTE_R21-27_ast_side_fstring_stack_pollution.md` §0/§6 replaced those with measured facts
(the junk is in the AST dict, the segment reducer refuses correctly, and the refusing window is the swept-in
statements), and its §6 measurement is what produced hunk 1. The register label for this unit,
`属性链截断`, describes the symptom; the cause was a prefix-window bound plus a call-chain arity assumption.

## 5. Banked, not landed, entering gate 36

R21-33 (`_trade_status_handle`) still needs both halves, with the analyzer `else_blocks` axis closed by two
measured variants (`PANEL`/ticket §5-§7); `_process_order` / `_process_cancel_order` keep their r25b
shrink-only banked candidate; the clock_worker M1/M2/M3b stack and r46a's quote analyzer half are unchanged.

## 6. Next gate

Label **36** against `rounds/round35/after`. **6 units in 3 files**: `trade_live_broker` 4
(`_process_order`, `_process_cancel_order`, `_sync_worker`, `_trade_status_handle`),
`realtime_event_source.clock_worker` 1, `quote.run_individual_transform` 1.
Session arc: gate 30 6603 → 31 6606 → 32 6608 → 33 6609 → 34 6610 → **35 6611 / 6617 (99.9093%)**,
399 green files.
