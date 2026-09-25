# Round 66 · diag4 · FACTS (live, written as measured)

Scope: risk_calculation `get_TradeMode_trades`, flyAccount `_do_request`,
order_api `option_order`/`future_order`. Read-only. Repo untouched.

## 0. baseline re-read (--arm=landed)  ✅ ALL IDENTICAL TO BRIEF

targets (dump/landed.jsonl, logs/landed_targets.log):
- `__init__.pyc` 32/35 mism=[[_on_publish_after_trading_end,486,481,3,33],[_save_testds_to_csv,71,68,7,19],[get_TradeMode_trades,1839,1801,4,1617]] sha=8f1e9d4ea252f808
- `flyAccount.pyc` 21/23 mism=[[_do_request,436,443,2,384],[init_connection,42,41,0,25]] sha=e58c7d8dbc8fdd25
- `order_api.pyc` 32/34 mism=[[future_order,101,92,2,36],[option_order,83,73,3,39]] sha=5e59c43ab22b72f1

battery (dump/battery_landed.jsonl): 24 items, matched sum = **91/104**, every per-file line equal
to brief (incl. r63b5_w1 init_connection, r64d5_contsink probe, r65_trytail p5, fs2 5/10, fsrepro 6/7). ✅

canary (dump/canary_landed.jsonl): sha per-branch identical to brief —
quotation 4d41187e356544e0 143/143; market_time af77224b34b203c4 10/10;
datetime_func e711b8ea86d49a15 26/26; datetime_func 9d09af09249da177 25/25. ✅

Repo line numbers re-verified by grep on CURRENT worktree bytes (`region_ast_generator.py`,
50410 lines; `region_analyzer.py` 27665 lines):
- `_loop_build_if_with_exit_branches` def L10470, single call L10014 (this is the R64 candidate R65 diag5 falsified)
- `_try_build_ternary_kwarg_call` def L42968, single call L37979
- `_apply_r23n6_return_promotion` def L47636, single call L46138

## 1. Hunk tables (normalized `nhunks.py --ctx=2`, dumps dump/hunk_*.txt)

### get_TradeMode_trades (risk_calculation) — dump/hunk_get_TradeMode_trades.txt
orig=1970 decomp=1928, **14 substantive hunks, ALL `delete` of exactly 3 instructions**, at orig
offsets `962/978, 1004/1026, 1052/1068, 1464/1480, 1506/1528, 1554/1570, 4816/4832`
(7 pairs; orig range 962..4850 inside the function, decomp 960..4684).
Deleted triples = `COPY COPY BINARY_SUBSCR` and `BINARY_OP(13,+=) SWAP SWAP`.
Reference compile on this interpreter (3.11.7): `d['k'] += 1` =
`LOAD c, LOAD k, COPY 2, COPY 2, BINARY_SUBSCR, LOAD v, BINARY_OP 13, SWAP 3, SWAP 2, STORE_SUBSCR`;
plain `d['k'] = v` = `LOAD v, LOAD c, LOAD k, STORE_SUBSCR` → 3.11 STORE_SUBSCR is value-first.
Product (build_landed/IQEngine__plugins__plugin_system_risk_calculation____init__OK.py
L604-606, L621-623, L721) = `'win_time'[1] = self.TradeMode_trade_statistic` for original source
L933 `self.TradeMode_trade_statistic['win_time'] += 1` → 缺语句(读回被丢) + 三操作数循环错位;
jump_diffs=4 while every hunk is a pure delete. Context stable: only the **then-arm of an `elif`
inside a `for` body ending in `continue`** is mangled; the sibling `else` arm with the identical
3 AugAssigns is correct (L609-611).

### _do_request (flyAccount) — dump/hunk_do_request.txt
orig=471 decomp=480 (overshoot), **21 hunks** = 9 `insert` (+2/+1 decomp-only instrs at
orig@292, 314, 1284, 1798, 2010, 2032, 2176 — all `POP_TOP; LOAD_CONST None` / duplicate-test
pairs) + 12 `replace` at orig@296/300, 1254/1258, 1326/1340, 1780/1784, 1992/1996, 2014/2018, 2168.
Product (fly__simtradding__flyAccountOK.py L135, L158, …) shows the shape
`(error_dict, {} if is_dict else [])` + `return None` where source is
`return error_dict, ({} if is_dict else [])` → **Return demoted to Expr**.

### option_order / future_order (order_api) — dump/hunk_option_order.txt, dump/hunk_future_order.txt
6 / 5 hunks (delete+replace+insert). Ground truth dump/dis_option_order.txt +
dump/dis_future_order.txt: both functions are
`strategy_log.info('…'.format(order_id=…, symbol=…, side=<ternary>, oper=<ternary>[, hedge_type=<ternary>]))`
guarded by `if not is_trade():` — **2 inline ternaries in the MIDDLE of a 5-kwarg `.format()`**;
the product loses the whole `strategy_log.info(...format(...))` statement and emits the ternary
tests as free-standing Expr fragments (order_apiOK.py L206-245).

## 2-4. get_TradeMode_trades — ATTRIBUTED, SYNTH REPRO, SPEC (candidate d1aug)

### 1. hunk table (see §1 above): 14 pure deletes = 7 lost `COPY COPY BINARY_SUBSCR` +
###    7 lost `BINARY_OP(+=) SWAP SWAP`. Product text = `'win_time'[1] = self.Trade...`.

### 2. Attribution — `sys.settrace` call counter (trace_count.py, read-only, dumps in
dump/trace_synth.txt + the runs quoted below). Both `_split_subscr_operands` call sites were
separated by **caller frame line number**, not by guessing:

synth (synth/r66d4_augsub.pyc, landed arm), `_build_subscript_assign` 3 hits /
`_split_subscr_operands` 3 hits:
```
{"fn":"_split_subscr_operands","lineno":2624,"caller":"_generate_block_statements_body@44371",
 "expr_instrs":"[128 LOAD_FAST, 130 LOAD_CONST, 132 COPY 2, 134 COPY 2, 136 BINARY_SUBSCR,
                146 LOAD_CONST, 148 BINARY_OP 13, 152 SWAP 3, 154 SWAP 2]"}
 -> RET ([128], [130], [132..154])          # rotated: value=container, container=key, index=rest
{"fn":"_build_subscript_assign","lineno":49198,"caller":"_build_effective_stmts@2817",
 "instrs":"[232 LOAD_FAST,234 LOAD_CONST,236 COPY 2,238 COPY 2,240 BINARY_SUBSCR,250 LOAD_CONST,
           252 BINARY_OP 13,256 SWAP 3,258 SWAP 2,260 STORE_SUBSCR]"}
 -> RET {'type':'AugAssign','target':{'type':'Subscript', ... 'slice':'lost' ...},'op':'+'}
```
=> the 3 CORRECT statements go through `_build_effective_stmts` (L2756), whose STORE_SUBSCR
   handler carries the `[R102 fix]` augmented-store gate at **L2798-2821** (def of the delegate
   `_build_subscript_assign` at **L49198**);
   the 3 MANGLED statements are in a `BlockRole.CONTINUE` block and go through
   `_generate_block_statements_body`'s own copy of the STORE_SUBSCR splitter at
   **L44369-44371** which calls `_split_subscr_operands` **without** that gate →
   `_split_subscr_operands` (def **L2624**) cuts (value, container, index) by net stack effect,
   the 2 SWAPs make the boundary land one slot early, and the result is
   `Assign(targets=[Subscript(value=key, slice=rhs)], value=container)`.
   Sibling un-gated copy: **L44569-44571** (`BlockRole.LOOP_BACK_EDGE`) — same defect shape,
   0 hits on this pyc.

Real corpus (`.../plugin_system_risk_calculation/__init__.pyc`, landed, all 35 functions):
`_split_subscr_operands` hits by caller = `8 × _generate_block_statements_body@44371`,
`4 × _build_effective_stmts@2825` (the latter are genuine plain stores, gate already ran),
`0 × @44571`. 7 of the 8 = the 7 mangled statements, so the un-gated site is the whole defect.

### 3. Synthetic repro `synth/r66d4_augsub.py` (14 lines) → `synth/r66d4_augsub.pyc`
landed: `probe 94/78, 4 jump_diffs, 62 true_diffs`, product =
`'win'[1] = s / 'profit'[a-b] = s / 'tot'[1] = s` in the elif+continue branch,
`s['lost'] += 1 …` correct in the sibling else branch → **same shape as the target**.
dump/hunk_synth_augsub.txt: 6 pure 3-instruction deletes. candidate arm: `2/2` (see §5).

### 4. Spec `specs/cand_r66_d1_augsub_continue.json` — single file, single anchor
anchor (count==1 asserted on LF text, taken from landed bytes L44369-44371):
```
                        if _instr.opname == 'STORE_SUBSCR' and len(_eff_expr_instrs) >= MIN_INSTRS_FOR_SUBSCR_ASSIGN:
                            # 栈效应切分支持多指令容器（data.loc = LOAD+LOAD_ATTR）。
                            _split = self._split_subscr_operands(_eff_expr_instrs)
```
+23 lines: the identical `[R102 fix]` stack-protocol predicate (in-place BINARY_OP arg>=13 with a
following SWAP + a COPY arg>=2 = the 3.11 read-back protocol) delegating
`_eff_expr_instrs + [_instr]` to the same-level `_build_subscript_assign`, falling back to the
existing split when it returns None. Three-part 识别条件/归约方式/AST 映射 comment included;
no name/offset/threshold match, no cross-region containment, nothing suppressed.
`h62.py build --dst=d1aug` → `head pristine == worktree bytes` (repo untouched), BOM+CRLF kept.

## 5. Measured A/B (h62.py ab) — arm d1aug vs landed


targets : `IMPROVED …plugin_system_risk_calculation/__init__.pyc 32/35 -> 33/35`
          `TALLY SAME=2 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`
          (get_TradeMode_trades disappeared from mism → fully matched;
           `_do_request` / `order_api` unchanged)
battery : `TALLY SAME=24 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`, sum 91/104 = baseline ✅
canary  : `TALLY SAME=4 …`, 4/4 shas byte-identical (4d41187e356544e0, af77224b34b203c4,
          e711b8ea86d49a15, 9d09af09249da177) ✅
synth   : `IMPROVED …r66d4_augsub.pyc 1/2 -> 2/2`
dumps   : dump/d1aug_targets.jsonl, dump/d1aug_battery.jsonl, dump/d1aug_canary.jsonl,
          dump/d1aug_synth.jsonl; logs/d1aug_battery.log


### candidate-arm confirmation (build_d1aug/)
synth: all 6 statements now AugAssign (`s['win'] += 1`, `s['profit'] += a - b`, `s['tot'] += 1` in
both arms), file 2/2.
target: product L604-606 become `self.TradeMode_trade_statistic['win_time'] += 1` etc.
`_do_request` dump also saved read-only to dump/probe_mr_do_request.txt (8 TernaryRegion,
merge_context is None × 7).

## 6. 402 full-corpus shards (`D:/Temp/opencode/r65gate/all402.txt`, --nshard=4 --shard=0..3)
Both arms run completely (101+101+100+100 = 402 files each), every shard command <290 s.
dump/landed_402_s{0..3}.jsonl, dump/d1aug_402_s{0..3}.jsonl, merged *_402_all.jsonl.

```
IMPROVED F:/…/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc  32/35 -> 33/35
TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
landed 402: functions matched 5693/5746, fully-matched files 385, errors 0
d1aug  402: functions matched 5694/5746, fully-matched files 385, errors 0
```
Per-shard A/B: s0 SAME=101, s1 IMPROVED=1 SAME=100, s2/s3 included above; **zero MOVED,
zero ERR, zero REGRESSION across all 402 files.** No branch left untested.

## 7. Excluded branches — 候选：NONE for `_do_request` and for `order_api`
(measured readings, dumps: dump/hunk_do_request.txt, dump/probe_mr_do_request.txt,
logs from trace_count runs quoted in §1-2 of the report)

### _do_request — R65 intel **partly confirmed, partly FALSIFIED**
* CONFIRMED: `probe_mr.py` (read-only, live analyzer on the code object) — `_do_request` has
  33 regions, **8 TernaryRegion, exactly 7 with `merge_context is None`**
  (entries @280, @296, @1254, @1310, @1770, @1992, @2014; the 8th @2056 has merge_context='str'),
  which is exactly the 7 demotion sites ≈ the 21 normalized hunks. Field evidence, same layer.
* FALSIFIED (new for R66): the repair path does **not** die on its POP_TOP test. Runtime counter:
  `_apply_r23n6_return_promotion` (def L47636) is reached **4×** (all from
  `_generate_block_statements_body@46138`), all return None, and the **return-site line numbers**
  (f_lineno at the 'return' trace event) are `47665, 47665, 47668, 47665` — i.e. it bails at the
  except-context gate (L47661-47665, roles seen `BlockRole.IF_THEN`, `IF_ELSE`, `TRY_BODY`) and at
  the last-statement-is-Expr gate (L47667-47668). The POP_TOP test at L47670-47683 is
  **never reached (0 hits)**.
* Why no candidate here: the demotion decision lives in `region_analyzer.py`
  (`merge_context` is assigned in the region-classification block L21661-21968), i.e. one layer
  above the AST generator; the only generator-side hook is that except-context gate, and any patch
  that widens it to `IF_THEN/IF_ELSE/TRY_BODY` would promote *every* trailing discarded Expr in
  every if/try arm to a `Return` — that is not a structural identity, it is an "emit more"
  suppression-class heuristic on a global path (POP_TOP is precisely the marker that the value was
  discarded), so it is excluded by the rules rather than by taste. 候选：**NONE**.

### order_api option_order / future_order — R50 family re-measured, no new same-level predicate
* CONFIRMED by runtime counter: `_try_build_ternary_kwarg_call` (def L42968) fires **2×** (once per
  function) from `_generate_ternary@37979`, and both calls return None **at L43098** — the
  `for i, name in enumerate(kw_names)` kwarg-slot bail ("Would need preload kwarg value").
  That is the exact defect line.
* Why no candidate here: fixing it requires reconstructing the *non-ternary* kwarg values, which
  live (a) in the ternary cond_block prefix (order_id, symbol), (b) **after** the merge block
  (share=order_.amount at orig@424) and (c) in an outer `strategy_log.info(...)` call closed at
  orig@526-540 with POP_TOP — i.e. three different stack depths across two region layers plus a
  nested outer call. Any predicate that keys on "some kw_names slots have no ternary" without that
  reconstruction is a name/slot-position heuristic, and the reconstruction itself is not a
  same-level structural identity (it needs cross-region containment of the merge block's tail).
  R50/R55 already measured the narrow versions INERT/worse. 候选：**NONE**.

## 8. Repo integrity
`git status --porcelain | grep -c "^ M"` → **0 modified tracked files**; the only entries are
pre-existing untracked artefacts from earlier rounds. Every write went to
`D:/Temp/opencode/r66gate/diag4`. `h62.py build` asserted
`mirrors built: head pristine == worktree bytes` for the candidate build.

## 9. Deliverables
* FACTS.md (this file)
* specs/cand_r66_d1_augsub_continue.json — 1 spec, 1 file, 1 anchor, +23 lines
* synth/r66d4_augsub.py + .pyc + synth/r66d4_augsub.txt (repro list)
* dump/: landed.jsonl, battery_landed.jsonl, canary_landed.jsonl, d1aug_targets.jsonl,
  d1aug_battery.jsonl, d1aug_canary.jsonl, d1aug_synth.jsonl, synth_landed.jsonl,
  landed_402_s0..3 + d1aug_402_s0..3 + *_402_all.jsonl, hunk_*.txt, dis_*.txt, trace_synth.txt,
  probe_mr_do_request.txt
* logs/: landed_targets.log, landed_battery.log, d1aug_battery.log, landed_402_s*.log,
  d1aug_402_s*.log
* tools (workspace-only): trace_count.py (sys.settrace call/return counter with caller-line
  attribution), probe_mr.py (merge_context field dumper), make_spec1.py (spec generator that reads
  the anchor out of the landed bytes)
