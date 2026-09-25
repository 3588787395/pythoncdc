# Round 66 · diag1 · FACTS (running log)

Target batch: `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
Landed baseline from BRIEF: **106/119**, 13 defect functions.

Repo is read-only for me. All writes here in `D:/Temp/opencode/r66gate/diag1`.

## Step 0 — landed baseline replay

All three landed replays are BYTE-IDENTICAL to BRIEF baselines:
- targets: 106/119, 13 mismatches exactly as listed. `build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py`
- battery: 24 files, matched 91/104, per-file readings identical.
- canary: quotation 143/143 sha=4d41187e356544e0, market_time 10/10 sha=af77224b34b203c4,
  datetime_func 26/26 sha=e711b8ea86d49a15, datetime_func 25/25 sha=9d09af09249da177.  (all 4 shas match)

## Step 1 — normalized hunk tables (nhunks.py, jumps->J, codeobjs->CODEOBJ)
`build_landed/…trade_live_brokerOK.py`; logs in `logs/hunks/<fn>.txt`.

| function | orig | decomp | nhunks | shape |
|---|---|---|---|---|
| _process_cancel_order | 344 | 344 | 6 | del NOP@44; replace@1606 (JUMP_FORWARD); rep@1710; del 2@1822; ins 2@1926; rep 2@2040 |
| _process_order | 520 | 464 | 27 | del NOP@44 + 14 scattered "delete" hunks (56 instrs lost) + 4 "insert" |
| _sync_worker | 412 | 410 | 8 | del 22@362, del 18@544, ins 6@526, del 2@868, ins 4@686, big misalign, del 165@1890 |
| _trade_status_handle | 130 | 126 | 3 | del 10@44(NOP+get_trade_status), ins 6@774(while-cond), rep 2@870 |
| after_trading_cancel_order | 177 | 180 | 2 | rep 1->2@164; ins 2@170 |
| etf_basket_order | 769 | 769 | 2 | **PURE MOVE**: del 11@1328 / ins 11@2448 — identical 11-instr block |
| etf_purchase_redemption | 427 | 415 | 5 | rep 4->1@2274, del 1@2312, del 1@2328, rep@2340, del 7@2424 |
| get_all_orders | 87 | 90 | 2 | del 4@346, ins 7@438 |
| get_etf_stock_info | 157 | 159 | 1 | ins 2@10 (prologue) |
| get_max_amount | 218 | 233 | 1 | ins 15@1016 |
| ipo_stocks_order | 1206 | 1214 | 14 | del 1@2810, ins 1@2886, rep@3258, ins 2@3380, ins 1@3446, ins 1@3466, ins 1@3510, **del 15@3524**, rep@3886, rep@3934, ins 1@3946, del 1@5006, **del 28@5476**, ins 45@6094 |
| on_order_response | 511 | 509 | 3 | del 1@2148, **ins 15@2374**, **del 16@2642** |
| on_trade_response | 448 | 446 | 3 | del 1@1766, **ins 15@1992**, **del 16@2260** (identical shape to on_order_response) |

Notes:
- `delete orig[7:8]@44 (NOP)` appears in `_process_cancel_order`, `_process_order`, `_trade_status_handle`
  at the same index/offset -> same shape, but a NOP is emission noise not a statement.
- `on_order_response` / `on_trade_response` share an *identical* 3-hunk signature (del 1, ins 15, del 16).
- `etf_basket_order` is a pure 11-instruction relocation, no content change.

### ATTRIBUTION CANDIDATE A — `get_etf_stock_info` (144/146, jd=1, true=139): single hunk, cleanest

orig (L2024..) vs decomp (L1343..), from `logs/gesi_orig.txt` / `logs/gesi_decomp.txt`:
```
ORIG                                                    DECOMP
 6 LOAD_FAST etf_code                       L2026         6 LOAD_FAST etf_code
 8 POP_JUMP_FORWARD_IF_FALSE to 12                       8 POP_JUMP_FORWARD_IF_FALSE to 16
10 JUMP_FORWARD to 56                        L2027      10 BUILD_LIST        <- SPURIOUS (L1344)
12 LOAD_GLOBAL strategy_log                  L2029      12 STORE_FAST in_stock  <- SPURIOUS
...                                                      14 JUMP_FORWARD to 60
56 BUILD_LIST                                              BUILD_LIST
58 STORE_FAST in_stock                                    STORE_FAST in_stock
```
Decomp = orig + exactly the 2 instrs `BUILD_LIST / STORE_FAST in_stock` (orig 56/58, the statement
AFTER the join) duplicated INTO the empty then-branch.

Proof of the true source shape (measured, CPython 3.11.7, `dis` of a synthetic):
`if etf_code: pass` `else: <warning; return>` `in_stock = []` emits
`LOAD_FAST etf_code / POP_JUMP_FORWARD_IF_FALSE to ELSE / JUMP_FORWARD to JOIN` where the JUMP_FORWARD
carries starts_line == the line of `pass`, and `pass` emits **zero** instructions.
-> orig's `10 JUMP_FORWARD to 56  L2027` is literally the `pass`.  So the true source is
```
2026  if etf_code:
2027      pass
2028  else:
2029      strategy_log.warning('未传入ETF代码，查询失败')
2030      return info_out
2031  in_stock = []
```
The decompiler instead printed `in_stock = []` inside the empty then-branch **and** after the if.
Root cause class: **an empty sibling branch region is filled by stealing the statement that
follows the if/else join** -> duplicate emission (+2 instrs, orig count preserved elsewhere).
Restoring `pass` reproduces orig byte-exactly (0 instructions for `pass`).

### ROOT CAUSE NAMED (landed bytes, measured)
`F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py`
 - `def _merge_block_is_then_exclusive` at **line 16809** (W15-C judgement).
   Its statement-free-arm filter is lines **16841-16849** (`_noise_ops` loop over `region.then_blocks`);
   the BFS that only tests *forward reachability of the false exits* is lines 16850-16900+.
 - `def _if_generate_normal` at line **17290**; the absorbing use-site is **line 17916-17936**:
   `if (merge_block is not None and self._merge_block_is_then_exclusive(region)
        and not (then_stmts[-1].type in Break/Continue/Return/Raise)): … then_stmts = _kept + _merge_then_stmts`
   (`_kept` explicitly drops the synthetic `{'type':'Pass'}`, line 17934-17935.)
 Runtime proof (`probe_gesi3.py`): for `get_etf_stock_info` IfRegion@0
   `_if_generate_then_branch` returns `[{'type': 'Pass'}]`  (correct, arm is source `pass`)
   `_if_generate_normal`   returns If(body=[Assign in_stock=[] @L2031], …)  -> the Pass was replaced.
 `_process_if_blocks` never produced that statement; only the merge-block absorption did.

### SYNTHETIC REPRO (measured, landed)
`synth/r66_empty_then_join.py` -> `synth/r66_empty_then_join.pyc`, list `synth_r66.txt`
landed reading: **2/3**, mismatch `[["j1", 17, 16, 1, 12]]`
product `build_landed/D___Temp__opencode__r66gate__diag1__synth__r66_empty_then_joinOK.py`:
```
def j1(cond, log):                 # BUGGY, same shape as get_etf_stock_info
    out = {}
    if cond:
        in_stock = []              <- absorbed from the join block
        return in_stock
    else:
        log.warning('bad')
        return out
def j2(cond, log):                 # NEGATIVE CONTROL, already correct
    total = 0
    if cond:
        pass
    else:
        log.info('ok')
    total = 1
```
j1: else-arm TERMINATES (`return out`) => join block unreachable from false exits
    => `_merge_block_is_then_exclusive` returns True => join absorbed.
j2: else-arm falls through to the join => BFS reaches it => returns False => `pass` kept.
So the discriminator between the two is **inside the region itself**: j1's then arm
(`then_blocks=[block]`) has that block's only instruction = `JUMP_FORWARD -> merge_block`
(the codegen signature of a source-level empty arm, verified in the 3.11.7 experiment above,
where `pass` emits 0 instrs and the arm is exactly `JUMP_FORWARD to JOIN` tagged with the
`pass` line), whereas j2/W15-C true-body arms reach the join by fall-through.

### DISCRIMINATOR (measured; my first guess was WRONG and is recorded so nobody repeats it)
Probe `probe_guard.py` / `probe_guard2.py` over targets+battery+canary+synth (29 pyc, full
`generate()`): `_merge_block_is_then_exclusive` returns True exactly **7** times.
```
  file                            fn                        then     else     merge  jump_to_mb
  trade_live_broker.pyc           <module>/TradeLiveBroker/  [10]     [12]     56     True
                                  get_etf_stock_info
  repro_r63b2_tail_cmp_return.pyc <module>/case_elif_try_    [1276]   [1278]   1282   True
                                  tail_return
  r66_empty_then_join.pyc         <module>/j1                [10]     [12]     58     True
```
- Rejected criterion #1: "an arm block's last instr is an unconditional JUMP_* into merge_block".
  Measured `jump_to_mb` is True for **all 7**, incl. the legitimate W15-C witness -> would break it.
- Rejected criterion #2: "`else_blocks` empty". Measured: both shapes are `region_type=IF_THEN_ELSE`
  with non-empty else_blocks (r63b2 else=[1278]) -> no separation.
- **Accepted criterion (same-level, reuses the existing predicate):** apply the *existing*
  "does this arm contain a statement" filter (`_noise_ops` + `JUMP*`/`POP_JUMP*`, generator
  L16843-16850) once more, to the region's OWN `else_blocks`.
  Measured `else_stmt_free`: buggy 5 hits -> **False** (else arm holds real statements),
  W15-C witness 2 hits -> **True** (else arm is `POP_TOP + JUMP_BACKWARD`, the chained-compare
  false-exit cleanup; `chained_compare_blocks=[1266]`).  5 flipped / 2 kept — perfect separation.
  Reasoning that makes it a structural identity: CPython 3.11 lays a *non-empty* then-body
  physically between the test and the else body, so "statement-free then arm + statement-bearing
  else arm" can only come from source `if cond: pass`; the merge block is then the parent
  sequence's continuation, not the arm's body.

## Step 2-5 — SPEC `specs/cand_r66_e1.json` and measured A/B

Spec: single file / single anchor / 1 edit, `core/cfg/region_ast_generator.py`,
anchor = the `_noise_ops` statement-free-arm filter at L16843-16850 (LF-normalised
`count==1`, verified). Replacement appends the `[R66-diag1 E1 …]` guard (35 lines) that
re-applies the *same* predicate to `region.else_blocks` and returns False when the else arm
does contain a statement. Three-part comment (识别条件 / 归约方式 / AST 映射) is inside the patch.

`h62.py build` output: `mirrors built: head pristine == worktree bytes, cand patched
(1 edits, core/cfg/region_ast_generator.py, BOM=True, nl=CRLF)` — the head-vs-worktree byte
assertion passed, so the repo was not modified by this round.

### Measurements (`--arm=cand`)
targets: **107/119** (landed 106/119). Mismatch list loses `get_etf_stock_info`; the other 12
entries keep their exact landed numbers:
`[["_process_cancel_order",293,292,16,43],["_process_order",454,396,9,349],["_sync_worker",349,347,0,296],
["_trade_status_handle",114,112,0,107],["after_trading_cancel_order",155,155,3,122],
["etf_basket_order",693,693,11,216],["etf_purchase_redemption",377,369,1,37],["get_all_orders",79,78,2,24],
["get_max_amount",201,213,2,18],["ipo_stocks_order",1075,1076,10,437],["on_order_response",445,444,6,57],
["on_trade_response",392,391,6,57]]`

Product `build_cand/…trade_live_brokerOK.py` now reads exactly like the true source:
```
        info_out = {}
        if etf_code:
            pass
        else:
            strategy_log.warning('未传入ETF代码，查询失败')
            return info_out
        in_stock = []
```

### Formal A/B (`h62.py ab`)
| list | command | result |
|---|---|---|
| targets | `ab --a=dump/landed.jsonl --b=dump/cand.jsonl` | IMPROVED 106/119 -> 107/119 · SAME=0 IMPROVED=1 **REGRESSION=0** MOVED=0 ERR=0 |
| battery  | `ab --a=dump/battery_landed.jsonl --b=dump/battery_cand.jsonl` | **SAME=24** IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0, fully-matched a=17 b=17 (91/104 unchanged) |
| canary   | `ab --a=dump/canary_landed.jsonl --b=dump/canary_cand.jsonl` | **SAME=4** REGRESSION=0 — all four shas byte-identical landed vs cand: 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 |
| synth    | `ab --a=dump/synth_landed.jsonl --b=dump/synth_cand.jsonl` | IMPROVED 2/3 -> 3/3 · REGRESSION=0 |

Battery/canary SAME is sha-based, i.e. those 28 products are byte-for-byte unchanged by the patch.

## Step 6 — 402 full-corpus shards
### FIRST CANDIDATE REJECTED BY THE 402 (recorded; battery missed it)
Variant 1 of the guard = "else arm contains a statement" only. Measured A/B on `all402.txt`
(`dump/a402_landed.jsonl` 402 files 0 errors sum_matched=5693 fully-matched=385 vs
`dump/a402_cand.jsonl` 402 files 0 errors sum_matched=5693 fully-matched=384):
`TALLY SAME=400 IMPROVED=1 REGRESSION=1 MOVED=0 ERR=0`,
regression = `strategy.pyc 24/24 -> 23/24`, function `tick_worker_thread` (268/269, jd15, true144):
`elif '11:30:00' < dt_strf < '12:30:00': time.sleep(60)` lost its body (`pass`) and
`time.sleep(60)` got hoisted after the whole if/elif chain. NOT variant-able: rejected.

### FULL-CORPUS FIELD TABLE (probe_cc.py over all 402; W15-C returns True 26 times)
| shape | cc (chained_compare_blocks) | else arm stmt-free | needs absorption |
|---|---|---|---|
| slippage/create_new_price/check_and_return | [96] non-empty | True | YES (legit) |
| check_strategy ×2 | [820]/[1180] non-empty | True | YES |
| handlers/perform_rollover ×2 | [] empty | True (else_blocks=[]) | YES (`rt=IF_THEN`) |
| strategy/tick_worker_thread ×2 | [552]/[1022] **non-empty** | **False** | YES (the variant-1 victim) |
| scheduler | [1366] non-empty | True | YES |
| **trade_live_broker/get_etf_stock_info ×3** | [] **EMPTY** | **False** | **NO (the bug)** |
Corroborating (not used in the patch): the buggy merge block (56) is `block_to_region`-owned by a
sibling `IfRegion@56` (entry == merge), while every legit case's merge is owned by an enclosing
`TryExceptRegion`/`LoopRegion` — i.e. only the buggy one is re-emitted by the parent sequence.
=> **Accepted guard = AND of two same-level reads of the region's own fields:**
(2) the existing statement-free filter applied to `region.else_blocks` says the else arm DOES
contain a statement, AND (3) `region.chained_compare_blocks` is empty (single-test condition, so
no compare-chain rotation can explain the statement-free then arm).
This flips exactly 3/26 corpus hits (all three = the get_etf_stock_info code object reached from
module / class / method traversals) and leaves 23/23 legit hits intact.

### FINAL CANDIDATE `specs/cand_r66_e1.json` (variant 2 = else-arm-has-statement ∧ chained_compare_blocks empty)
`h62.py build` -> `mirrors built: head pristine == worktree bytes, cand patched
(1 edits, core/cfg/region_ast_generator.py, BOM=True, nl=CRLF)`; anchor `count==1`; +43 lines.

| list | A/B result |
|---|---|
| targets | IMPROVED 106/119 -> **107/119** · SAME=0 IMPROVED=1 **REGRESSION=0** MOVED=0 ERR=0 |
| battery (24) | **SAME=24** IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0 · fully-matched a=17 b=17 · 91/104 unchanged |
| canary (4) | **SAME=4** REGRESSION=0 · shas 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 — all four identical to the BRIEF baseline |
| synth (3) | IMPROVED 2/3 -> **3/3** REGRESSION=0 |
| **402 full corpus** | **SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0** · landed 5693/5746 matched, cand **5694/5746** · fully-matched files a=385 b=385 · 0 errors both arms · `--nshard=4 --shard=0..3`, every command < 300 s |

## Summary
- Attributed (13/13 hunk tables in `logs/hunks/`; one deep attribution):
  `get_etf_stock_info` -> `core/cfg/region_ast_generator.py`
  `_merge_block_is_then_exclusive` L16809 (filter L16843-16850) + use site `_if_generate_normal`
  L17916-17936. Root cause: the W15-C "join block is the then arm's true body" judgement also
  fires for a **single-test if/else whose then arm is a source-level `pass`**, so the block after
  the join gets absorbed into the empty arm and re-emitted there (duplicate emission).
- Repro: `synth/r66_empty_then_join.py` -> `.pyc` (`j1` reproduces, `j2` is the already-correct
  fall-through control). Landed 2/3 -> cand 3/3.
- Spec: `specs/cand_r66_e1.json` (1 file, 1 anchor, 1 edit). Battery 24 + canary 4 + 402 files all
  non-regressing. 402 was mandatory: it caught variant 1's regression on `strategy.pyc`.
- Not attributed / left open in this batch (readings in the table above): `_process_order` (58 lost
  instrs = the known R65 f-string `_(f'…')` family, `[R64-B2]`/`[R65-d3 C1a-C1c]` region — explicitly
  out of scope here), `ipo_stocks_order`, `etf_basket_order` (pure 11-instr relocation),
  `_sync_worker`, `on_order_response`/`on_trade_response` (identical del-1/ins-15/del-16 signature =
  a nested if/else hoisted out of its parent then-arm to the sibling join — separate rule, not
  diagnosed to a line within this round's budget), `_trade_status_handle`, `_process_cancel_order`,
  `after_trading_cancel_order`, `etf_purchase_redemption`, `get_all_orders`, `get_max_amount`,
  `get_etf_stock_info`'s sibling cases.
