# Round 22 修复（fixes）：R22-A = J1′ ＋ J2′ ＋ J3′

设计见 `arm-design.md`。本轮落地**只改两个文件**：`core/cfg/region_analyzer.py`、
`core/cfg/region_ast_generator.py`；不改生成产物、不改脚本、不改索引条目以外的任何文件。

## 一、落地方式（可复现）

镜像谱（`D:/Temp/r23prep/`、`D:/Temp/r23diag/`，全部零仓库写入）：

```
mirror/base  = git archive 46e752ab core bytecode pycdc.py _r10_strict_check.py | tar -x
实测候选     = mirror/j123 = base + J1′ + J2′ + J3′（三块补丁；最小复现电池在它上面判 PASS）
落地规格     = landing/build_final2.py landing/spec_r22_v2.py
              （base→mirror/j123 的行级 hunk，每段 3 行上下文 + 两处纯注释改动）
落地         = landing/apply_spec.py landing/spec_r22_v2.py --write
```

`apply_spec.py` 的约束：白名单只允许这两个文件；每个锚点 `count(old)==1` 否则立即退出；按目标
文件的 EOL 约定还原 CRLF（两文件均纯 CRLF，行尾不被改写）；写后以内存 `compile()` 做语法自检
（不产生 `__pycache__`）。

写盘后与工作树复验（`probes/proof_landed_vs_cand.py` → 日志 `proof_landed.txt`）：工作树与
"被电池实测过的候选"之间只允许差在注释行上。

```
core/cfg/region_analyzer.py      worktree 59b70fa360d19ad0  cand 59b70fa360d19ad0  differing_lines=0   code_identical=True
core/cfg/region_ast_generator.py worktree a203dd17fe82f824  cand e7f2272e629f0b77  differing_lines=15  code_identical=True
```

15 行 = `+6 / −9`：`_discover_predicate_and_chain` docstring 新增「第三条守卫（链首落点判据）」
一段（+5）并把「两条守卫都只删不增」改成「三条守卫」（±1）；`_is_orphan_boundary_nop`
docstring 删掉已失效的 `V-M (条件汇合锚点)` 条目（−8）。`code_identical` 的判据是**剥掉
docstring 后的 AST dump 相等**（注释不进 AST，docstring 显式剥离），故三处改动的可执行代码
与实测候选逐节点相同。

第一次落地写的是 J2r（§二末尾），电池判 FAIL 后 `git checkout --` 回退这两个文件，再按上表重写。

## 二、三处代码改动

### J1′ `core/cfg/region_analyzer.py` `_identify_conditional_regions`（17129 段）

```
-                if not _25b_else_is_cond and self._if_arm_is_sink(then_blocks, then_stop):
+                # R13c 守卫细化（同层结构化判据，禁止跨区域启发式）：
+                # (a) 作用域分裂 …  (b) 共享隐式出口 …（注释全文见文件）
+                _25b_arm_loop = self._find_enclosing_loop(then_blocks[0])
+                _25b_else_loop = self._find_enclosing_loop(else_succ)
+                _25b_same_loop = _25b_arm_loop is _25b_else_loop
+                _25b_shared_rn = (any(self._is_return_none_block(b) for b in then_blocks)
+                                  and any(self._is_return_none_block(s)
+                                          for s in else_succ.successors))
+                if (not _25b_else_is_cond and _25b_same_loop and not _25b_shared_rn
+                        and self._if_arm_is_sink(then_blocks, then_stop)):
                     merge = else_succ
```

### J2′ `core/cfg/region_ast_generator.py` `_discover_predicate_and_chain`（16368-16383，链收集完成、`return {'blocks': chain, 'op': 'and'}` 之前）

```
+        # [J2 守卫·同层结构判据] or 短路汇合点识别：链首块若是**另一个纯操作数
+        # 求值块**（复用既有 _chain_block_is_pure）前向条件跳转的落点，则该链首是
+        # `X or <本 and 链>` 的右操作数入口 …（注释全文见文件）
+        _head = chain[0]
+        for _pj in _head.predecessors:
+            if _pj in chain or _pj.start_offset >= _head.start_offset:
+                continue
+            _pl = _pj.get_last_instruction()
+            if (_pl is not None and _pl.argval is not None
+                    and _pl.argval == _head.start_offset
+                    and _pl.opname in FORWARD_CONDITIONAL_JUMP_OPS
+                    and self._chain_block_is_pure(_pj)):
+                return None
         return {'blocks': chain, 'op': 'and'}
```

**被否决的加强版 J2r**（在上面那条合取式里再加 `self.region_analyzer.get_entry_region_for_block(_pj)
is not None`，或其 `_pj in region.blocks or …` 析取变体）：语料级看它**严格优于** J2′ —— 全量 402
pyc、严格尺子，两版都是 `n_ok +15 / improved=10 / broken=0`，J2r 还多赚 4 条幅度且 `worse=0`
（J2′ 有一处 `api_base` 幅度退化，见 §三）。但它被本轮的最小复现电池判死：判据更严 ⇒ 放弃重建
的情形更少 ⇒ `if a and b or c and d or e and g:` 这类"中间析取支"形状不再命中，左半
`a and b or c and d` 整体丢掉（锚点 `r22_16_j2_andor_three_disjuncts` NOT-FIXED，`orig=17 decomp=9`）。
两种写法的电池日志 `D:/Temp/r23prep/batt_j2r.txt`、`batt_r3.txt`（各 `FIX=16/17  FAIL=1  GATE: FAIL`）。
语料里不存在这个形状，所以只有电池能看见它 —— 取舍理由与形状分析见 `arm-design.md` §二。

### J3′ `core/cfg/region_ast_generator.py` `_is_orphan_boundary_nop`

删掉 V-M 那条判据（其循环体里的 `for blk in self.cfg.get_blocks_in_order()` 全 CFG 扫描）
与其 docstring 条目：

```
-                # [A4/V-M] 条件跳转以本 NOP 自身为汇合目标（argval == nop_off）： …
-                if (bi2.opname in CONDITIONAL_JUMP_OPS
-                        and getattr(bi2, 'argval', None) == nop_off):
-                    return False
```

只删不增；余下 V-T/V-S/V-B/V-L 四条与本方法 docstring「以下四类结构性 NOP」重新自洽。

## 三、落地前的全量实测（严格尺子，402 文件 × 两世界）

记录：`D:/Temp/r23prep/ab/{base,j123}_decomp/chunk_*.jsonl`（各 402 条）、
`D:/Temp/r23diag/ab/{base,j123r2}_decomp/`（被否决版），汇总复算 `probes/blind_mag2.py`。

```
base   files=402  n_ok=5989  sum|delta|=1857
j123（落地版）    n_ok=6004(+15)  sum|delta|=1776(-81)  improved=10  broken=0  worse=1
j123r2（J2r，否决）n_ok=6004(+15)  sum|delta|=1772(-85)  improved=10  broken=0  worse=0
```

10 个文件的逐函数缺陷被消除（`[seq_len]` 读数消失＝该函数逐指令全等）：

```
IQCommon/api/klinedata.pyc                         np_tp_pd 169→167, to_pd_result 185→183 消除
IQCommon/util/common_func.pyc                      to_pd_result 185→183 消除
IQData/plugins/plugin_system_realquote/real_quote  get_real_daily_kline 210→212, get_real_minute_kline_bk 169→171 消除
IQEngine/plugins/plugin_fly_data/__init__.pyc      ApiMethodPlugin.resist_api 107→105 消除
IQEngine/plugins/plugin_fly_data/fly_api/history_api  to_pd_result 185→183 消除
IQEngine/plugins/plugin_system_persist/json_persistance  JsonPersistance.persist 78→76 消除（该文件转全匹配）
IQEngine/plugins/plugin_system_trade/trade_live_broker   cancel_order 89→71 消除
fly/common/flytools.pyc                            get_mem_under_oom_status 47→18, whitelist_filter 116→114 消除
fly/common/market_time.pyc                         MarketTime.trade_is_open 97→89 消除
fly/data/quote_handler.pyc                         get_all_fundamentals_daily / get_all_valuation /
                                                   get_all_valuation_new 各 73→71 消除；
                                                   get_kline_local 760→676 收窄为 760→682
```

退化面唯一一处，如实登记：`IQData/api/api_base.pyc` 的 `get_history_df` 幅度 `1742→1722` 变
`1742→1718`（该文件 `sum|delta|` 36→40，`n_ok` 25→25 不变 ⇒ 官方尺不变，索引该条目维持 23/25）。
其余 391 个文件逐函数读数不变。

## 四、门禁（按固定顺序，逐条贴工具原始输出）

0. 最小复现电池（37 复现，before/after 双镜像核，`test_repros/round22_drift/run_all.py`）：

```
BATTERY :: repros=37  FIX=17/17  GUARD=15/15  RESIDUE=5/5  REVIVED=0  FAIL=0  ERROR=0
GATE: PASS                                     （日志 D:/Temp/r23prep/batt_landed.txt）
```

1. `single` 修到完全 OK（两条，本轮靶子文件）：

```
$ python scripts/pyc_batch_verify.py single site-packages/IQEngine/plugins/plugin_system_persist/json_persistance.pyc
  total_functions:   7      matched_functions: 7      match_rate: 100.00%
$ python scripts/pyc_batch_verify.py single site-packages/fly/common/market_time.pyc
  total_functions:   10     matched_functions: 10     match_rate: 100.00%
```

2. `quotation.pyc`：

```
$ python scripts/pyc_batch_verify.py single site-packages/fly/data/quotation.pyc
  decompile_status:   partial
  total_functions:   143    matched_functions: 142    match_rate: 99.30%
    - change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377
```

（该唯一缺陷自 Round 21 收尾起读数不变，本轮未变差。）

3. 全量复验 `batch --index pyc_index.json --all --round 22`（`include_ok=True`，402/402 全跑）：

```
[BATCH] index=pyc_index.json, max_count=None, round=22, include_ok=True
[BATCH] total=402, pending=402, round=22, include_ok=True
...
  ok_pyc:                362
  partial_pyc:           40
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5633
  cumulative_match_rate: 98.03%
```

4. `python scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                362
  partial_pyc:           40
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5633
  cumulative_match_rate: 98.03%
```

**索引被这一步改动的条目**（相对 `46e752ab` 时刻，共 4 条；Σ`function_count` 仍是 5746）：

```
IQCommon/manager/instance.pyc                               29/32  -> 31/32
IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  103/119 -> 104/119
fly/common/custom_tools.pyc                                  6/6   ->  5/6    （ok -> partial）
IQCommon/util/trade_info_utils.pyc                          40/40  -> 38/40    （ok -> partial）
```

后两条不是本轮造成的：`arm-design.md` §一的逐提交二分显示它们自 `f89b85f2`（Round 13）起就是
43/46，本轮只是第一次把它们复验回实测。前两条是本轮的真实增益（`instance` 原本是索引低估）。

本轮对已发布序列的效果：`arm-design.md` §一实测过，**落地前**用旧核实测只有 5621/5746（索引写
5633，虚高 12 个函数、5 个 `ok` 标记）；**落地后**实测回到 5633/5746 = 98.03%，`ok_pyc` 从实测
359 回到 362。⇒ 序列上的数字与上一轮相同，但这个 5633 现在是复验出来的实测值，不再是停在
Round 10 的旧标记。
