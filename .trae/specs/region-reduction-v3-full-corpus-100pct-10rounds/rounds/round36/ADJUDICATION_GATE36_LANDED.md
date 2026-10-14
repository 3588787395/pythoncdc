# Gate 36 adjudication and landing record — R21-33 CLOSED, broker `_trade_status_handle` landed

Landed: `core/cfg/region_analyzer.py` `35e227ac3e7b25af` → **`efd455859b69d8a1`** (17 lines at
`:5948`, inside `_is_while_true`) and `core/cfg/region_ast_generator.py` `87910190b7ef7c35` →
**`37997bdac555b2e9`** (29 lines at `:13387`, inside `_loop_handle_no_exit_successors`). Both are
needed; neither flips alone (measured below), so this is a two-half criterion, not a single edit.

## The defect, and why only the pair closes it

`trade_live_broker._trade_status_handle` was sealed at `len orig=127 prod=124 delta=-3 hunks=3`.

1. **The loop is not `while cond … else`.** Decided by `compile()` on this interpreter
   (`rounds/round36/shape_tails2.py`), not by reading: the original's signature is `NOP @44` as the
   continue target, ONE top test `POP_JUMP_FORWARD_IF_FALSE → 830`, an unconditional
   `JUMP_BACKWARD → 46` at the end of the stream and NO trailing `LOAD_CONST None/RETURN_VALUE`
   (its only `return None` tail, `@448`, is the one inside the TRADE_STOP arm). Our emitted
   `while … else` compiles with the test TWICE (top `POP_JUMP_FORWARD_IF_FALSE` + bottom
   `POP_JUMP_BACKWARD_IF_TRUE`) and appends a return tail — that is the `+5` and part of the `+2`.
   So the analyzer criterion: a header block's conditional jump whose landing block ends in a
   `JUMP_BACKWARD` onto that same header keeps BOTH exits inside the cycle, therefore the test is a
   nested `if` and the loop is `while True`.
2. **The landing block is the `if`'s merge, not an else arm.** Census
   (`D:/Temp/r36/region_census_r36b.py`): `@830` = `time.sleep(0.5)` + `JUMP_BACKWARD → 46`,
   predecessors `{@46 (the cond block), @720, @722}` — entered from inside the then side too. The
   generator's `_loop_handle_no_exit_successors` rendered it as `if not cond: time.sleep(0.5);
   continue` placed BEFORE the body (site pinned by line trace `D:/Temp/r36/who_negates_r36.py`:
   `If`-constructing lines executed = `[13415, 16438, 20756, 22639]`, the negated arm from `13415`).
   The fix emits `If(test, body=<then suite>)` with the merge rendered immediately after it, which
   is the original's position.
3. **The then suite must use the suite renderer.** Hunk C used `_generate_block_statements(_then_succ)`
   and is a measured **regression** (`-85/2`): that call renders one block's own instructions and
   never dispatches the nested regions living in it, so the body leaked flat at loop level. C2 uses
   `self._if_generate_branch_stmts(blocks=...)` — the same call the loop body renderer uses at
   `:14640` — over the loop's declared `body_blocks` minus the header block and minus the merge, so
   no membership is invented and the children (`IfRegion IF_THEN cond=@150..184 merge=@296`,
   `IfRegion IF_ELIF_CHAIN cond=@318..338 merge=@830`) are dispatched normally.

## Per-half measurements (mirror, sealed products as the reference)

| build | `_trade_status_handle` | broker file |
|---|---|---|
| sealed gate-35 | `delta=-3 hunks=3` | 124/128 |
| hunk A alone (gen `7344dcc566442e58`, STORE_ATTR/STORE_SUBSCR boundary) | `delta=+6 hunks=2` (the `del=9 @46..@90` hunk closed) | 124/128, 19/20 panel files byte-identical |
| hunk B alone (analyzer `efd455859b69d8a1`) | `delta=+1 hunks=2` | 124/128 |
| hunk C (gen `7a02cc2a06d55447`) + B | `delta=-85 hunks=2` — FALSIFIED | 124/128 |
| **hunk C2 (gen `37997bdac555b2e9`) + B** | **`delta=0 hunks=0`** | **125/128** |

Hunk A is subsumed by B for this unit (under `while True` the statements go through
`_loop_process_header_instructions`, which already has the `STORE_ATTR` boundary rule), so A stays
banked: `CANDIDATE_r36_R21-33a_store_split_BANKED_not_landed.py`, certified corpus-wide at zero
flips earlier in this round (see `ADJUDICATION_GATE36_ZERO_FLIP_REVERTED.md`).

## Other broker units before/after (the ticket's duty: perturbing them is a regression)

| unit | sealed gate-35 | B+C2 |
|---|---|---|
| `_trade_status_handle` | −3/3 | **0/0 → Equal** |
| `_process_order` | −465/4/1 | **−68/14** (still failing, 397 instructions restored) |
| `_process_cancel_order` | −293/3/0 | **−1/3** (one instruction from Equal) |
| `_sync_worker` | −3/5/6 | −3/5 (unchanged) |
| `ipo_stocks_order` | 0/0/0 | 0/0 |
| `get_ipo_stocks` | 0/0/0 (landed r54a) | 0/0 |
| `etf_purchase_redemption` | 0/0/0 (landed gate 35) | 0/0 |

## Chain (single clean run)

`gate_chain.py 36 35`, log `D:/Temp/gate_chain_36_075427.log`:
regen **ok=402 bad=0** (203 s) → verify rc=0 174 s → report → checks 156 s, `CHAIN_DONE`:

```
[units] 6611/6617 -> 6612/6617  (99.9244%)   [files] 399 -> 399
[gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=1
[quotation] 153/153 | [small34] units_success 1563 (was 1562: moves by exactly the flip count)
[selfcheck] 153/153 Equal, 常量变异 1/153, 极性变异 1/153 | [pytest] 2 failed 282 passed 2 xpassed (only the two registered residents)
```

20-file pre-gate panel for B+C2 (`D:/Temp/t30/log_panel_r36full2.txt`): 19 files byte-identical to
the sealed products, only broker moves; unit counts `153/153 91/92 64/64 30/30 58/58 41/41 28/28
45/45 27/27 37/37 125/128 17/17 12/13 43/43 49/49 39/39 43/43 17/17 15/15 18/18` — zero decreases,
including all six duplicated-module canaries.

## Residual sealed after this landing (`residual_report.py 36 35`, 08:03:51, UNREGISTERED=0)

单元 **6612/6617 (99.9244%)**, 文件 **399/402**, 残余文件 **3**, 残余单元 **5** (was 6):
`realtime_event_source.clock_worker` 12/13 · `trade_live_broker._process_order` ·
`trade_live_broker._process_cancel_order` · `trade_live_broker._sync_worker` ·
`quote.run_individual_transform` 91/92.

Next: `_process_cancel_order` is now `delta=-1` — the cheapest unit in the corpus. Then
`_sync_worker` (-3/5, relocation), `clock_worker` (M1+M3b re-anchored at `3d4f27de6d80ab6e` gives
−113/7 → −3/8, the residual is one relocation of ~106 instructions plus a lost 17-block),
`run_individual_transform` (r46a analyzer half, −52 → 0), and `_process_order` (−68/14).
