# Round 67 · diag1 · FACTS (read-only diagnosis)

Workspace `D:/Temp/opencode/r67gate/diag1`. Repo `F:/Downloads/pythoncdc-main` is **read-only**
for this task: no writes to `core/`, `*OK.py`, `pyc_index.json`, `.trae/`, `test_repros/`.
All artefacts live in this directory. No 402-file sweep run here.

Discipline actually used: every command `python -X utf8`, **PYTHONIOENCODING never set**, each
command self-sharded to finish <300 s.

## Target batch (from BRIEF, do not re-derive)
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
official 107/119 (gap 12), strict 105/123 (18 defects, missing 0, extra 0).

---

## STEP 0 — baseline replay on CURRENT landed bytes (`--arm=landed`)

Commands (run fresh, dumps were empty at session start):

```
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl
python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/landed_battery.jsonl
python -X utf8 h62.py run --arm=landed --list=canary.txt  --out=dump/landed_canary.jsonl
```

(results appended below in "Step 0 results")

### Step 0 results — ALL THREE BASELINES REPRODUCE on current landed bytes (session start, repo clean)

`git status --short core/` in the repo: empty (no tracked modification) => landed bytes == R66 landing.

**targets** (5.4 s): `107/119`. All 12 OFF rows identical to BRIEF, row by row incl. jumpdiff/truediff:
```
_process_cancel_order 293/292 j16 t43 | _process_order 454/396 j9 t349 | _sync_worker 349/347 j0 t296
_trade_status_handle 114/112 j0 t107 | after_trading_cancel_order 155/155 j3 t122 | etf_basket_order 693/693 j11 t216
etf_purchase_redemption 377/369 j1 t37 | get_all_orders 79/78 j2 t24 | get_max_amount 201/213 j2 t18
ipo_stocks_order 1075/1076 j10 t437 | on_order_response 445/444 j6 t57 | on_trade_response 392/391 j6 t57
```

**battery**: CORRECTION TO MY OWN WORKSPACE, not to the brief — the `battery.txt` copied into this
workspace was a stale **24**-line list (R65 era) giving 93/104. Rebuilt it from the 31 rows the brief
prints (all 31 paths verified to exist). Re-run at landed: **115/127, 12 defect functions**, and every
per-file row equals the brief's row verbatim (c6 50/50 j1 t15, c8 31/33, d2 44/45, d8 51/50, init_connection
42/41, probe 122/122 j1 t9, p5 33/30 j2 t20, v1/v6/v7/v8, v6 36/34 j2 t16). Stale copy kept as
`battery_stale24.txt.bak`. => brief baseline CONFIRMED.

**canary** (7.6 s): 4/4 shas **byte-identical to the brief**:
```
quotation.pyc      143/143 sha=4d41187e356544e0   market_time.pyc     10/10  sha=af77224b34b203c4
datetime_func.pyc   26/26  sha=e711b8ea86d49a15   datetime_func.pyc   25/25  sha=9d09af09249da177
```
Sanity cross-check with the public gates at the same bytes: `python -m test_repros.smoke_battery
--arm=landed` -> 110/110 (that runner's own list is 110 items, a different set from the 31-item
centre battery; recorded so the two numbers are never confused); `test_repros/run_p5_gate.py` ->
PASS (3/3, 9/9, 2/2). All read-only.

---

## STEP 1/2 — hunk verdicts + attribution (measured on landed bytes)

### verdict table (nhunks, jump args -> `J`, nested code -> `CODEOBJ`)
| function | orig/decomp instr | verdict | evidence |
|---|---|---|---|
| `get_all_orders` | 87/90 | **纯换位 + 重复发射** (join region hoisted into inner then-arm, one stmt emitted twice) | delete `orig[22:26]` = `JUMP_FORWARD; LOAD_FAST self; LOAD_ATTR all_orders; STORE_FAST result`; insert `decomp[43:50]` = same store moved to function tail + **two** `LOAD_CONST None; RETURN_VALUE`; listcomp `return` appears twice (product L2552/L2553) |
| `_trade_status_handle` | 130/126 | **块坍缩/归属** (NOT emission order) | delete `orig[7:17]@44`(10 instrs: `NOP; get_trade_status(trade_id=self.trade_id, X=True); self.trade_info=`), reinserted near tail; product L911 shows a *different* 1-arg `get_trade_status(self.trade_id)` — two distinct call sites collapsed into one. Not a displacement family. |
| `etf_purchase_redemption` | 427/415 | 5 hunks, all in one 150-instr tail region @2274-2424 | not chased (counts unequal, tail-local) |
| `v1`,`v2`,`v4`,`v5`,`ok1` synth | equal | **pass at landed** | region shape alone does NOT reproduce |

### attribution for the `get_all_orders` family — measured, corrects my own first guess
Region tree of `get_all_orders` (logs/blk_get_all_orders.txt) and of synth `v3`
(logs, `blk.py`) are **isomorphic**:
```
IfRegion entry@0    merge_block@98  exit@98   then=[12,16,84,20,68]  else=[]      parent=None
IfRegion entry@12   merge_block@98  exit@98   then=[16,20,68]        else=[84]    parent=IfRegion@0
LoopRegion entry@20 blocks=[16,20,22,68]      header@20                          parent=IfRegion@12
IfRegion entry@98   merge=None      exit=None then=[102]             else=[106,148,176] parent=None
```
i.e. the region tree is **RIGHT**: blk@98 (`if c is None:`) is a top-level sibling whose entry
*is* the enclosing if-regions' merge/exit. Only the emitted AST is wrong.

**Falsified lead of mine (do not re-try)**: I first suspected R66-diag1 E1 /
`_merge_block_is_then_exclusive` (generator L16834-16845, E1 marker L16876). Measured with
`e1probe.py`: it returns **False for all three IfRegions** in `get_all_orders` (entry@0, @26, @362)
and for all three in `v3`. E1 is not involved; this is a different family.

**Real emission site (measured by wrapping all 244 generator methods, `ctr2.py`)**:
```
_if_generate_then_branch IfRegion@12 -> _process_if_blocks IfRegion@12
  -> _generate_region LoopRegion@20 -> _generate_loop -> _loop_generate_for
       -> _loop_generate_body (blocks 16,20,22) -> _loop_postprocess
       -> _generate_region IfRegion@98   *** called from region_ast_generator.py:21935 in _process_if_blocks ***
```
So the join region is emitted **from inside the for-loop's statement list**, then inherits the
inner if's then-arm indentation. The call site is the generic structured-region entry detector:
`_region = self.region_analyzer.get_entry_region_for_block(block)`
`if isinstance(_region, _STRUCTURAL_REGION_TYPES): ... _ast = self._generate_region(_region)`
at L21928-21947 (docstring L21922-21927 says it exists for "standalone 模式 (region=None，如 loop
else body 调用)"), with no guard that the entry block it is looking at is the **current statement
sequence's own** block rather than a block that belongs to the enclosing if/else's merge point.

### minimal synthetic repro (STEP 3) — DONE
`synth/r67_join_after_noelse.py` -> `synth/r67_join_after_noelse.pyc`, list `synth_r67.txt`.
At `--arm=landed`: **6/7**, defect `v3` `orig=43 decomp=42 jumpdiff=2 truediff=23`
— same fingerprint as `get_all_orders` (`79/78, j2, t24`). `v3` hunk table is the *same shape*
(delete 4 @82 incl. `JUMP_FORWARD`+else-arm store; insert 7 @164 = that store + two
`LOAD_CONST None; RETURN_VALUE`). `v1/v2/v4/v5/ok1` all pass at landed => the two necessary
ingredients are (a) then arm of the inner if/else is **multi-block containing a LoopRegion whose
tail block jumps straight to the if-region's merge**, (b) an if/else arm exists (`else=[84]`).

---

## STEP 4/5 — candidate J1 measured, and REJECTED by the gates

spec `specs/cand_r67_j1.json` (1 edit, anchor `count==1` verified before build,
`h62.py build` reports "head pristine == worktree bytes"). Predicate = three same-frame /
own-field reads only, at generator L21928-21934 inside the standalone structured-region
entry detector: `(region is None) ∧ (self._current_loop is not None) ∧ (_region.parent is None)`,
comment carries 识别条件 / 归约方式 / AST 映射. No names, files, offsets, thresholds, no
cross-region `entry in r.blocks` containment, no new self state, no "don't emit" (the region
returns to its own owner, the top-level region loop at L1754, and is emitted exactly once).

Measured (all arms re-run in this session, same lists):

| gate | landed | J1 | verdict |
|---|---|---|---|
| synth `synth_r67.txt` | 6/7 (v3 43/42 j2 t23) | **7/7** [] | repro fixed, defect gone |
| targets `trade_live_broker.pyc` | 107/119 | **ERR** `RuntimeError('Failed to decompile ...')` | **GATE FAIL** |
| battery (31) | 115/127, 12 defects | `SAME=31 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` | no regression, no gain |
| canary | 4/4 sha as brief | `SAME=3 MOVED=1` — quotation.pyc still 143/143 but **sha != 4d41187e356544e0** | **GATE FAIL** (canary must be byte-identical) |

Reproducible reading of the ERR: the same mirror decompiles the target file fine when
`mirr_j1` is put first on sys.path in a fresh process without `PYTHONPATH`
(`OK len 168821`), so the failure is not a plain crash in the patch — under the harness the
`continue` at the guard leaves a standalone call that claims nothing and the enclosing loop
path then re-enters the same block set (the target contains loops whose standalone tail calls
hit clause (3) far more often than the synth does). Narrowing lead for the next round, measured
but not built: add a fourth same-level conjunct that the standalone block list is a **single**
block equal to `self._current_loop`'s successor-of-tail **and** that
`_region.entry.get_first_instruction().offset` is the enclosing IfRegion's own `merge_block`
offset — i.e. restrict to the `blocks=[98]` shape read off the current frame's own `blocks`
argument, which is exactly `standalone blocks=[98] owner=Region@98 _region=IfRegion@98 parent=None`
as captured above.

## BATCH VERDICT

**候选：NONE（本轮不提交可落地判据）** — J1 is the measured reason: it eliminates the
`get_all_orders`/`v3` defect class on the repro (6/7→7/7) with the battery untouched, but it
breaks the named target outright (ERR) and moves a canary sha, so it cannot be landed as-is.
Step-0 baselines, per-function hunk verdicts, the falsified E1 lead, the attribution to
L21928/21935 with the captured frame context, and the repro are all reproducible above.
Unfinished by budget: hunks of `_process_order` (454/396, 缺语句 family — the largest real loss
left) and the `ipo_stocks_order` / `etf_basket_order` / `after_trading_cancel_order`
equal-count displacement family were **not** attributed; `_trade_status_handle` was
(falsified as a displacement case — it is a two-call-site collapse onto one emission).

---

## STEP 1/2 — diag1b continuation

Scope handed over: `_process_order`, `etf_purchase_redemption`, and the equal-count family
(`ipo_stocks_order`, `etf_basket_order`, `after_trading_cancel_order`, `on_order_response`,
`on_trade_response`). `get_all_orders` / L21928-21947 untouched (fix1 owns it). Baselines
were re-verified by fix1's handoff note as settled; not re-run here except where a candidate
is measured.

### 1. `_process_order` — 缺语句, single cause, ATTRIBUTED (not displacement)

`python -X utf8 nhunks.py <pyc> build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py _process_order --ctx=3`
-> raw counts orig=520 / decomp=464 (official 454/396: same 56/58-instruction loss under the
harness's op filter), **27 substantive hunks**, full table in `logs/nh_process_order.txt`.

Interval reading (orig offsets, all inside the `try:` body of the `while len(self.open_orders)>0`
loop):

| orig interval | instrs | content | decomp counterpart |
|---|---|---|---|
| 626-684 | 11 | `strategy_log.error('可转债代码%s识别失败…' % order.symbol)` | **relocated** to decomp 2610 (= product L492, the `else:` arm) |
| 1638-1796 | 15+10 | `strategy_log.info(f"生成订单… {'买入' if order.entrust_direction==EntrustDirection.BUY else '卖出'} …")` | **lost**; only an empty-armed if/else remains at decomp 1620-1628 (both arms `JUMP_FORWARD to 2496`) |
| 2092-2160 | 8 | `strategy_log.info('生成订单…期权合约代码…'.format(...))` | **lost** |
| 2230-2234, 2304-2310, 2390-2396, 2430-2690 | 3+7+3+… | the `.format(side=… , oper=…)` argument ternaries and the enclosing calls | **lost**, skeleton at decomp 2052-2058 / 2124-2130 / 2266-2272 (arms compile to `NOP`) |
| 3168-3170 | 2 | loop back-edge `JUMP_BACKWARD to 46` | decomp ends with `LOAD_CONST None; RETURN_VALUE` |

Product-level proof (the emitted *source*, not a compile artefact): `build_landed/…trade_live_brokerOK.py`
L461-489 contains **9 bare string statements in if/else arms** —
`if order.entrust_direction == EntrustDirection.BUY:` / `"""买入"""` / `else:` / `"""卖出"""` — and
**no** `strategy_log.info(...)` line for them (grep `生成订单` finds L467 only, i.e. 1 of the 4 the
original has). Measured with `python -X utf8 -c "dis.dis(...)"` that a bare `Constant` str in
statement position compiles to **no instruction at all** (3.11 folds it), which is exactly why the
hunks read "arms that jump to the same join / NOP" instead of showing a lost ternary.
=> verdict **缺语句** (5 statements destroyed), one cause.

**Attribution (current landed bytes, measured with `sys.settrace` probe `ctr_r47.py`)**:
`core/cfg/region_analyzer.py` L22592-22603 — the `[R47 消费点守卫]`
`if (merge_block is None and value_target is None and not has_jump_forward_skip): return None`
(merge_block computed at L21581 by `find_nearest_common_post_dominator({true_block,false_block})`).

```
python -X utf8 ctr_r47.py <pyc> _process_order
REJECT cond@2574 true@2642 false@2646 merge=None value_tgt=None jfs=False
REJECT cond@2430 true@2568 false@2572 merge=None value_tgt=None jfs=False
REJECT cond@2310 true@2390 false@2394 merge=None value_tgt=None jfs=False
REJECT cond@2236 true@2304 false@2308 merge=None value_tgt=None jfs=False
REJECT cond@2092 true@2230 false@2234 merge=None value_tgt=None jfs=False
REJECT cond@1634 true@1754 false@1758 merge=None value_tgt=None jfs=False
```
6/6 candidates hit the guard, 0 pass. `regdump.py` (`logs/regdump_process_order.txt`) shows the
consequence at the same level: the tree contains **no TernaryRegion at all**; those six diamonds are
terminal `IfRegion@1634 blocks=[1634,1754,1758] then=[1754] else=[1758]`, `IfRegion@2236`,
`IfRegion@2310`, `IfRegion@2574` … i.e. two-arm diamonds *nested inside one statement* of
`IfRegion@1580 then_blocks=[1634,1754,1758,1760]`, and all 6 sit inside `TryExceptRegion@420`.
Every one of the six is a **pure IfExp diamond** (`true = LOAD_CONST+JUMP_FORWARD to F`,
`false = LOAD_CONST` falling into the same `F`, `F` consumes the value mid-expression:
`FORMAT_VALUE`/`BUILD_STRING` at 1760, `KW_NAMES/CALL` at 2310) — never a statement-level if/else.
NCPD returns None because each arm also has an exceptional edge out of the try body, so no block
post-dominates both arms: this is literally the case R47's comment cites ("try-except 内的
f-string inline if-else"), and the two existing merge recoveries (L21588 needs
`has_jump_forward_skip`, L21609 needs both arms to end in a *conditional* jump) do not cover it.

### 2. `etf_purchase_redemption` — 缺语句 + 假字面量, cause = f-string prefix window, NOT R47

`nhunks` -> orig=427 decomp=415, **5 substantive hunks, all inside one tail region 2274-2466**
(`logs/nh_etf_pr.txt`). `ctr_r47.py` shows its 2 ternary candidates (cond@1966 true@2384 false@2388
merge@2390 and cond@1856 true@1892 false@1896 merge@1898) both **pass** the R47 guard with
`merge_context='fstring'`, `value_target='__fstring_target__'` — so this function is *not* an R47
case; the loss is inside the fstring branch itself.

Orig tail (dumpfn, orig side) = 2 statements:
```
2274-2452  strategy_log.info(_(  '生成订单，订单号：' f'{order.order_id} 代码：' f'{order.symbol} 数量：'
                              f'{...' f'{abs(amount)'   -> BUILD_STRING@2422 PRECALL/CALL PRECALL/CALL POP_TOP
2454-2466  LOAD_FAST order; LOAD_ATTR order_id; RETURN_VALUE      (= `return order.order_id`)
```
Product L1594-1595 emits ONE statement instead of both:
`self.on_trade_response_list_handle(order)` then
`return f"list_info00orderstrresultentrust_noselforderorderselfstrorderselforderselforderstrategy_log_生成订单，订单号：{order!s} 代码：{order!s} 数量：order{'申购' … else '赎回'!s}{abs(amount)!s}"`.
The literal prefix is the *rendered names* of the finished statements L1588-1593 (`list_info`, `0`,
`0`, `order`, `str`, `result`, `entrust_no`, `self`, `order`, …, `strategy_log`) — i.e. the JoinedStr
prefix window starts at the head of the basic block instead of at the first instruction of the
in-flight expression, and the merge block's tail statement (`return order.order_id`) is consumed by
the same region. Site: generator fstring-prefix reconstruction inside the ternary 'fstring' merge
context — `region_ast_generator.py` L36213-36318 (`cond_val_start` stack-effect scan + L36260-36286
[R65-d3 C1a] callee skip + L36283-36318 the `LOAD_* -> 假字面量` loop), i.e. the **same** code the
landed [R66-d2 P3] marker L36319 extends. That makes it the R65/R66 f-string family the BRIEF
already assigns to P1/P3/P4, not a new layer: the missing piece is a *statement-boundary clamp* of
the prefix window (the span contains complete earlier statements whose CALL/POP_TOP pairs are
stack-neutral) plus the merge block's post-consumer tail. Verdict recorded; **no candidate here**
(would overlap the P1/P3/P4 layer without proving a different one).

### 3. Equal-count family — all 位移/换位, one shared shape; attribution by region-field evidence

| function | nhunks (raw) | verdict | interval record | unclaimed-arm evidence (regdump, landed) |
|---|---|---|---|---|
| `ipo_stocks_order` | 1206/1214, 14 hunks | **纯换位** (2 moves) + framing | delete `orig[720:735]@3524`(15: `POP_JUMP_IF_FALSE; strategy_log.error('账户无可转债交易权限…%s' % stock_code); JUMP_BACKWARD to 2380`) and `orig[1028:1056]@5476`(28: `JUMP_FORWARD to 5584` + `system_log.debug('代码：' f'{stock_code}' …)` chunk) → insert `decomp[1167:1212]@6094`(45) **after** `JUMP_BACKWARD to 2380` (loop back-edge) | tail arms emitted after the enclosing loop's back-edge |
| `etf_basket_order` | 769/769, **2 hunks** | **纯换位** (textbook: 11 out, same 11 in) | delete `orig[274:285]@1328` = `strategy_log.warning('该股票【%s】行情数据异常' % stock); POP_TOP; LOAD_CONST None; RETURN_VALUE` → insert `decomp[516:527]@2448`, immediately after `STORE_SUBSCR; JUMP_BACKWARD to 480` | `IfRegion@674 blocks=[674,698,806…1258,1276] then=[698] else=[806…1276] elif=[806]` — the if/elif chain's own **final `else` arm block@1328 is not in its `blocks`**, because its preceding arm ends in `RETURN_VALUE` (no successor to walk); 1328 is left to the outer `IfRegion@568`/`LoopRegion@480`, so it is emitted after them |
| `after_trading_cancel_order` | 177/180, 2 hunks | **多语句** (+3 instr: two `LOAD_CONST None; RETURN_VALUE` and an `EXTENDED_ARG`-widened `JUMP_FORWARD`) | replace `orig[33:34]@164` `JUMP_FORWARD to 168` -> decomp 164-166 `LOAD_CONST None; RETURN_VALUE`; insert `decomp[36:38]@170` another `LOAD_CONST None; RETURN_VALUE` | orig 158-166 is `then: order_param = order` + fallthrough to join 168 with `166 JUMP_BACKWARD to 132` as the *continue* arm (orig L3716-3718); the decompiler re-roles the arm as `return None` (decomp L2515-2518) — the continue/return role family (cf. landed `[R66-diag4 D1 augsub-continue-role]`), not a relocation |
| `on_order_response` | 511/509, 3 hunks | **纯换位** (15-instr arm pulled ahead; the 1-instr hunk is `EXTENDED_ARG` framing created by the move) | delete `orig[483:499]@2642`(16, starts with the `JUMP_FORWARD to 2742` that skips the arm) = `system_log.debug('…不接收非本交易触发的主推%s' % entrust_no); self.on_order_response_list.append(event)` → insert `decomp[438:453]@2374` **right after `COPY; POP_EXCEPT; RERAISE`** (the `except AttributeError` tail) | `IfRegion@2152 blocks=[2152,2220,2278,2338,2644] then=[2220,2278,2338] else=[2644] children=[TryExceptRegion@2278]` — the then-arm's *continuation* blocks `2376/2388/2550` (`if receive_other_response == '1' …`, orig-internal, i.e. between 2338 and the else arm 2644) are **not** in the region's blocks; they are listed as **siblings** (`LoopRegion@0 children=[… IfRegion@2146, IfRegion@2152, IfRegion@2376]`) although `IfRegion@2376`'s join (2742) *is* `IfRegion@2152`'s join. Product L992-995 shows the resulting dedent |
| `on_trade_response` | 448/446, 3 hunks | **纯换位**, identical fingerprint (delete 1 @1766 `EXTENDED_ARG`, insert 15 @1992, delete 16 @2260) | same chunk (`宿主机配置为策略不接收…` + `self.on_trade_response_list.append(event)`) at orig 2260-2356 vs decomp 1992 | `LoopRegion@0 children=[… IfRegion@2142?…]`; `IfRegion@1608/…` sibling pair at the same offsets (1522/1608/1610/1634/1762) — same shape as `on_order_response` |

**Shared cause statement (measured, all five):** the emitted *ordering* defect is not a jump-
relocation artefact — in every case the relocated span is a **block that the enclosing `IfRegion`
does not claim although the original control flow places it inside that region's arm** (its own
`then_blocks`/`else_blocks` stop before it, and it survives as a *sibling* child of the enclosing
`LoopRegion`). Two sub-shapes: (a) the preceding arm terminates unconditionally (`RETURN_VALUE` /
`RERAISE`) so the arm walk never reaches the next layout block — `etf_basket_order`,
`ipo_stocks_order`; (b) the inner region's join coincides with the outer region's join, so the
inner region is emitted as a sibling and dedented — `on_order_response`, `on_trade_response`.
`after_trading_cancel_order` is the exception: equal counts but a genuine **多语句** (+3) from the
continue/return role, so it is *not* in the relocation family.

Instruction-count note (so the two numbers are never confused): `nhunks.py` counts every
non-CACHE instruction (so `_process_order` 520/464, `etf_purchase_redemption` 427/415); the harness
`targets.md` numbers (454/396, 377/369) are the same lists under `pyc_batch_verify`'s own filter.

---

## STEP 4/5 — diag1b continuation: candidate `cand_r67_b1` written, built, measured → **不落地** (named-target gate fails)

### 4.1 Repro (≤15 lines, fails at landed with the `_process_order` fingerprint)

`synth/r67_r47_exitless.py` (u1-u5; u2 is the 8-line minimal form), compiled 3.11.7 →
`synth/r67_r47_exitless.pyc`, list `synth_r47c.txt`, dumps
`dump/landed_r47csynth.jsonl` (landed) / `dump/b1_synth.jsonl` (candidate).

* landed **1/6**: u1 51/44 j1 t43, u2 44/29 j0 t43, u3 41/29 j1 t39, u4 36/32 j1 t29,
  u5 59/59 (control, loop exit reachable). u1-u4 emit the same `if c: """P""" else: """Q"""`
  skeleton as `_process_order` product L461-489, and `ctr_r47.py` shows the same rejection
  (`[R47 消费点守卫]` with `merge_block=None, value_target=None, has_jump_forward_skip=False`)
  and the same degraded tree shape `IfRegion@54 blocks=[54,118,122]` ↔ `IfRegion@1634
  blocks=[1634,1754,1758]`.
* root cause measured with `pdom.py`: `while True:` gives the loop SCC no *normal* successor to
  an exit ⇒ 61 of 63 blocks keep `post_dominators == all blocks` ⇒
  `find_nearest_common_post_dominator` returns None for **every** block pair ⇒ no TernaryRegion
  anywhere in the function.

### 4.2 The predicate (same-level only) and its site

`specs/cand_r67_b1.json` → `core/cfg/region_analyzer.py`, anchor
`"                            merge_block = _t_ft\n\n            value_target = None\n            merge_context = None  # 新增: …"`
verified `count==1` on the LF-normalised utf-8-sig text (37 inserted lines; `h62.py build`
asserts all pass: 1 edit, head mirror == worktree bytes, CRLF consistent, inserted-line count).

Patch = one more member of the existing `merge_block is None` fallback family, appended right
after the four landed fallbacks (L21588 / L21609 / L21671 / L21713) and before the
`if merge_block:` classifier at L21769, so the landed classification (`merge_context`,
`value_target`), the `[R39]`/`[R39b]` purity guards and the `all_blocks` claim all run unchanged:

```
            if merge_block is None:
                _b1_exc_t = getattr(true_block, 'exception_successors', None) or set()
                _b1_exc_f = getattr(false_block, 'exception_successors', None) or set()
                _b1_norm_t = [s for s in true_block.successors if s not in _b1_exc_t]
                _b1_norm_f = [s for s in false_block.successors if s not in _b1_exc_f]
                if (len(_b1_norm_t) == 1 and len(_b1_norm_f) == 1
                        and _b1_norm_t[0] is _b1_norm_f[0]
                        and _b1_norm_t[0] is not block
                        and _b1_norm_t[0] is not true_block
                        and _b1_norm_t[0] is not false_block):
                    merge_block = _b1_norm_t[0]
```

Inputs are only the candidate's own three blocks; the `successors - exception_successors` filter
is *the same* definition `dominator_analyzer._compute_post_dominators` Option C already uses
(L157-167), and the "exactly one normal successor each, identical" shape is the same predicate
already written at L21016-21020. No names, no offsets, no thresholds, no cross-region
containment, no new `self` state, nothing suppressed.

### 4.3 Measurements (`h62.py ab` against the existing landed dumps)

| list | landed | b1 | reading |
|---|---|---|---|
| `synth_r47c.txt` | 1/6 | **3/6** | `ab`: IMPROVED=1. u2 44/29 t43 → **44/44 t1**, u1 51/44 → 51/57 (now over-emits), u3/u4 left the mismatch list |
| `battery.txt` (31 items) | 115/127, 24 files clean | **115/127**, 24 files clean | `ab`: **SAME=31**, improved=0 regressed=0 moved=0 |
| `canary.txt` (4) | 4 shas | 4 shas **byte-identical** | `ab`: SAME=4; `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177` all preserved |
| `targets.txt` (`trade_live_broker.pyc`) | 107/119 | 107/119 | `ab`: **MOVED** — gained `['_process_order', 454, 369, 8, 355]`, lost `['_process_order', 454, 396, 9, 349]` ⇒ the named target moves the **wrong** way (396→369 emitted, t349→t355) |

Gate set "canary byte-identical ∧ battery not worse ∧ named target better" is therefore **not**
satisfied ⇒ `cand_r67_b1` must not be landed. It still earns its record: it *proves* the STEP 1
attribution and isolates a second, independent missing piece.

### 4.4 What b1 proved about `_process_order` (and why it is not enough)

* With b1, `regarm.py b1 … _process_order` lists **6 TernaryRegions** where landed lists **0**
  (`@1634 mc='fstring' vt='__fstring_target__' merge=1760`, `@2092 mc='compare' merge=2236`,
  `@2236 mc='compare' merge=2310`, `@2310 merge=2396`, `@2430 mc='compare' merge=2574`,
  `@2574 mc='store' merge=2648`), and the product's bare-docstring skeletons drop from **25 to
  17** file-wide (`logs/diff_process_order.txt` shows the `"""买入"""/"""卖出"""` pair become
  `'买入' if … else '卖出'` inside the value context) ⇒ the R47 rejection really was the cause of
  the 缺语句 family, exactly as attributed in STEP 1.
* It still loses instructions, for a *different* reason that is now pinned down: the recovered
  join blocks host the value consumer **and** the following statements inside one physical
  block. Example `@2574` with `merge_block=2648` (`dumpfn.py … 2642 2760 orig`):
  `2648 LOAD_FAST order (L925) / 2650 LOAD_ATTR amount / 2660 KW_NAMES / 2662 PRECALL /
  2666 CALL / 2676 PRECALL / 2680 CALL / 2690 POP_TOP` ← consumes the two arm values, then
  `2692 LOAD_FAST order (L928) / 2694 LOAD_METHOD set_entrust_no …` = four *later* statements
  (`set_entrust_no`, `close_orders[…] = order`, `on_order_response_list_handle(order)`,
  `on_trade_response_list_handle(order)`). `TernaryRegion@2574 blocks=[2574,2642,2646,2648]`
  claims the whole block, and the only merge-block split that exists, `_mb_first_store_idx`
  (L21785-21794), cuts **only at `STORE_FAST/NAME/GLOBAL/DEREF`** — with a `CALL + POP_TOP`
  statement boundary it returns the whole block as the "effective prefix", so those four
  trailing statements lose their owner (confirmed: `set_entrust_no` present at landed L484-487,
  absent from the b1 product).
* Net: b1 is a *necessary* prerequisite, not a sufficient fix. The next candidate for this
  family is b1 **plus** a statement-boundary clamp of the claimed merge block (end the merge
  block's ownership at the first stack-neutral completed statement after the consumer —
  `CALL; POP_TOP` as well as `STORE_*`), which is a *different* site (the `all_blocks` claim
  walk ~L22400-22590 / the generator's merge-prefix reconstruction) and did not fit the
  remaining budget. Recorded as the hand-off with the numbers above.
* This also re-uses the STEP 2 finding: rendering the recovered ternaries is itself broken at
  landed (`f"股票strategy_log_生成订单，订单号：{order!s} …"` in the b1 product at L461; the same
  shape as landed L1594-1595 for `etf_purchase_redemption`) ⇒ the 假字面量 prefix-window family
  (generator L36213-36318, landed [R65-d3 C1a]/[R66-d2 P3]) that STEP 2 already assigned to
  P1/P3/P4. Both residual causes of `_process_order` therefore sit in the **f-string /
  merge-block-boundary** layer, not in the region-shape layer.

### 4.5 Per-function candidate verdicts (step 4 close-out)

| function | verdict | 候选 |
|---|---|---|
| `_process_order` | 缺语句 | `cand_r67_b1` **written + measured, 不落地** (target gate fails, §4.4) |
| `etf_purchase_redemption` | 缺语句 + 假字面量 | **NONE** — assigned layer is generator L36213-36318 (P1/P3/P4) |
| `ipo_stocks_order`, `etf_basket_order`, `on_order_response`, `on_trade_response` | 纯换位 | **NONE** here — cause is arm blocks left unclaimed by the enclosing `IfRegion` (terminate-arm / coinciding-join shapes, §3 table); needs an arm-completion predicate, a different site from B1 |
| `after_trading_cancel_order` | 多语句 (+3) | **NONE** — continue/return role family (cf. landed D1) |
| `get_all_orders` | (settled) | fix1's `_process_if_blocks` site; untouched |
| `_trade_status_handle` | (settled) | not a displacement case; untouched |

