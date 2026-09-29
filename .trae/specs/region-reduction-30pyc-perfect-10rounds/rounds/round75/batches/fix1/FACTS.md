# Round 75 · fix1 · F-ABSORB 61 单元修复批 — FACTS

工作区 `D:/Temp/opencode/r75gate/fix1` · 基线 HEAD **`3667987a`**（代码字节同 R74 落地 `982cd398`，
HEAD 只多 `.trae` 归档）· 臂 **`jqop1`** = `specs/jqop1.json`（`core/cfg/region_ast_generator.py`
3 edits / **+81 行** / BOM+CRLF 保留）· repo `F:/Downloads/pythoncdc-main` **本批零写入**
（`git status -- core scripts site-packages` 已跟踪文件零改动；未跑 402 全量；未手改任何 `*OK.py`）·
所有读数只写本区 `dump/`。

---

## 0. 结论一句话

在 `region_ast_generator._generate_block_statements_body` 的 **`_cjb_skip_inline_if` 分支**上找到
「块尾条件跳转的 fall-through 恰是某区域 entry 时，只发射前导语句就 `return`，把该块重建成的
**纯条件操作数 `_cjb_cond_expr` 丢掉**」这一根因；用**同层结构身份判据**（记录挂在 fall-through
入口块、消费端按 `region.entry` 取同一块对象）把操作数接回后继布尔链，
**mandated `jq_trans_module 63/65 → 65/65 failure→success`（mandate 达成）**，
官方 41 靶 `SAME=40 REGRESSION=0`、电池 82 项 `worse=0`、金丝雀 4/4、strict `NEW=0`、
G0 自检 12/12、synth 复现+负例 PASS，**影响面 = 161 份产物里只有 1 份（jq 本身）发生字节变化**。

---

## 1. 根因解剖（jq_trans_module 两个 `replace_args` 单元）

### 1.1 症状（mandated 尺 `pyc_verify single`）

```
status=failure units=63/65   失败两单元 = ***<module>.func_attribute_history_convert_code.replace_args
                                    + ***<module>.func_get_bars_convert_code.replace_args
判词：Failure: Different control flow
```

### 1.2 指令级差分（`fix1/probe_units.py`，opname+argrepr 精确对齐）

每个失败单元只有 3 处差，其中**只有一处是真缺陷**：

| # | 差 | 性质 |
|---|---|---|
| ① | `delete orig[99:103]` = `LOAD_FAST stock_tmp / CONTAINS_OP 0 / POP_JUMP_FORWARD_IF_FALSE … / LOAD_GLOBAL True…` 一段 4 指令 | **真缺陷**：产品少了条件首操作数 |
| ② | `LOAD_CONST` code object 的 `argrepr` 行号不同 | 判据忽略（比字节不比行号） |
| ③ | 1~2 个 `NOP` 差 | 判据忽略 |

**手改验证**（`fix1/probe_fixcheck.py`）：把落地 `*OK.py` 第 250/317 行条件前面加回
`'(' in stock_tmp and ` 后，`pyc_verify single` 读数 **63/65 → 65/65**。
⇒ 唯一阻塞项就是这个操作数。

### 1.3 条件的字节事实

原字节码条件（块 564/572/580/588，`IF_FALSE→580`、`IF_TRUE→596`、`IF_FALSE→716`、`IF_FALSE→716`，
`CONTAINS_OP arg` = `0,1,0,1`）：

```
'(' in stock_tmp and ')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp
```

落地产品（`jq_trans_moduleOK.py:250` 与 `:317`）：

```
')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp
```

即 **只有操作数 A `'(' in stock_tmp` 丢失**；B/C/D 三段极性本来就正确（勘误：早先推测的
「B/C/D 取反错」不成立，`_cjb_negate` 路径在本例未触发）。

### 1.4 结构事实（`fix1/probe_chain572.py`）

```
BoolOpRegion@572 blocks=[572,580,588] merge=716
  op_chain = [(572,'or',IF_TRUE→596), (580,'and',IF_FALSE→716), (588,'and',IF_FALSE→716)]
IfRegion@572   blocks=[572,596,716]  condition_block = 588
两区域同 entry = 块 572；get_entry_region_for_block(572) 优先返回 IfRegion（BoolOp 优先级 3 > If 2
后被 winner 规则反转），因此消费端是 BoolOpRegion、而 skip 分支拿到的 _er 是 IfRegion ——
这就是不能把记录挂在「区域对象」上、必须挂在**块**上的原因。
```

### 1.5 触发链（唯一、确定）

`_if_extract_condition_from_instructions`(:20669) → BoolOp 分支 `_build_boolop_expression`(:21116)
→ 结果写进 `boolop_region_for_cond.condition_expr`(:21200)；
`condition_expr` 的其余赋值点 :4585/:32026/:33671/:33693 **全部来自 `_build_boolop_expression`**
⇒ 只需在 `_build_boolop_expression` 外面包一层，即可覆盖所有缓存路径，不必改 :21104。

---

## 2. spec 设计（`specs/jqop1.json`，3 edits 全在 ALLOWED 文件）

| # | 锚点 | 内容 |
|---|---|---|
| 1 | `_generate_block_statements_body` :47629-47633 | 进入 skip 判定时置 `_cjb_pend_key = None`；确认 skip 时 `_cjb_pend_key = _cjb_then_entry`（**fall-through 入口块本身**） |
| 2 | 同函数 :47639-47643 | `return` 前：`pure_cond` 是非 `Constant True` 的 dict 时，`setattr(_cjb_pend_key, '_leading_operand', (expr, link_op, target))`；`link_op` 由 `('FALSE' in opname) != bool(negate)` 推出（`IF_FALSE`→`and`，`IF_TRUE`→`or`，取反则翻转） |
| 3 | `_build_boolop_expression` :32662 | 新增 `_contains_identity`（AST 身份幂等）、`_graft_pending_operand`（消费端）、把原函数改名 `…_inner` 并留一个先重建再嫁接的对外入口 |

### 2.1 同层结构身份判据（满足 BRIEF §4 硬规约）

- **配对键 = 块对象身份**：记录存 `entry_block._leading_operand`，消费端 `getattr(region.entry, '_leading_operand')`。
  记录与消费是**同一个块对象**，不跨层（不使用 `region.entry in r.blocks`），也不经过任何上层区域。
- **去向由 `op_chain` 链内位置判定**：跳转目标 ∈ 链成员 → 按位置（`ck==1` 且链首自成一组时接进首组）；
  目标 ∈ 链出口/`merge_block` → 整体 `BoolOp(link_op, [operand, expr])`；否则**原样返回**。
- **无新增 self 状态**：不使用 `self._cjb_pending_operand`（第一版曾用，被硬规约挡掉并已重做），
  新增的只有普通方法（`self._contains_identity(...)` 是方法调用不是状态）。
- **无**函数名 / 文件名 / 偏移阈值 / 名字白名单：`_graft_pending_operand` 里没有出现
  `replace_args`、`jq_trans`、`.py`、`start_offset <op> <int>` 任何字面量。
- **三要素注释**：edit3 docstring 含 ①根因（丢弃点 + 退化表达式 + 63/65）②同层身份判据
  ③去向与守卫（链内位置 + `_contains_identity` 幂等）。

### 2.2 影响面论证（为什么敢说零回归）

- 记录**只在丢弃分支**写入 ⇒ 没发生丢弃的单元根本不会有记录 ⇒ 不可能被嫁接。
- 发生丢弃的单元本来就 `Different control flow`（少 4 条指令 ⇒ 判据必红）⇒ 嫁接只会往正确方向走。
- 实测：**161 份产物（官方 41 + 缺陷 34 + 电池 82 + 金丝雀 4）里只有 jq 一份 sha16 变化**。

---

## 3. 门禁读数（全文 `dump/gates75_fix1.txt`）

| 闸 | 读数 | 判 |
|---|---|---|
| b 官方 41 靶 `h62 ab` | `SAME=40 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，fully matched `a=33 b=33`；MOVED=jq（`gained=[] lost=[]` 仅 sha 变） | PASS |
| c mandated focus | `jq 63/65 → 65/65 failure→success`；`klinedata 61/64 → 61/64`、`wizard 55/58 → 55/58`、`order_api 34/37 → 34/37`、`real_quote 43/45 → 43/45`（**0 新增失败**） | PASS（≥1 支转绿） |
| d 金丝雀 | `3eb76e512df9ab1e` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177` 全中，**4/4** | PASS |
| d battery | 82 repro `landed` vs `jqop1`，**worse-than-landed 0** | PASS |
| e sstrict | 34 pyc / 1528 函数：`defects 69 → 67`，**NEW=0**，RESOLVED=2（正是 jq 两个 `replace_args`），CHANGED=0，errors=0 | PASS |
| §2.2 hunks | `get_tick_direction` landed `hunks_norm=3` → jqop1 `3`（不升）；`get_real_minute_kline 6 → 6`；该文件 sha 与落地逐字节相同 | PASS |
| §4 G0 | `dump/g0audit.txt` **12/12 PASS**（三要素 / 无 self 状态 / 无跨层 / 无名字白名单 / 无偏移阈值 / ast+py_compile / BOM / repo 零改动） | PASS |
| synth | `repro75_jqcond` head `4/5 failure` → jqop1 `5/5 success`；`neg75_jqcond` 两臂 `sha=93a467678d39ec2c` **逐字节相同**且两侧 `3/3 success` | PASS |

---

## 4. 61 单元 a–e 子机理归属表（F-ABSORB）

来源：diag1 `submech75.py`（LIVE analyzer 结构证据）× `fam75.json`（首分歧判词），
原文 `dump/submech75.txt`（71 行 TSV，本区有副本）。flag 语义：`orphan` 孤儿子块、
`mergeabs` 共享尾被吸收、`outpred` 集外前驱（三者 >0 即命中对应子机理）。

**分布（61 单元）**：`a-shared-merge-absorbed 34` / `b-orphan-child 11` / `a2-shared-tail-extpred 7` /
`d-displacement 5` / `c-target-diff-instr 4`。
**flag incidence**：`mergeabs>0` 34、`orphan>0` 22、`outpred>0` 47、三 flag 全零 9（= c4 + d5）；
`mergeabs ∧ orphan` 并存 11（A∩B，改守卫须同批回归 orphan）。

**逐文件聚合**：

```
trade_live_broker 11 (a7/a2 2/c1/d1)   quote 8 (a5/a2 1/c1/d1)
klinedata 3 (a2/b1)                    wizard_quant_api 3 (a1/d2)
order_api 3 (a2/a2 1)                  jq_trans_module 2 (b2)   <- 本批靶
trade_info_utils 2 (a1/a2 1)           calexrights_func 2 (a2)
real_quote 2 (a2)                      __init__ 2 (b2)
future_contract_info 2 (a2)            ptradeAccount 2 (b2)
finance/email/api_base/bar/strategy_universe/history_api/strategy/realtime_event_source/
matcher/quotation/quote_handler/load_daily 各 1 (a)；handlers/cgroup_utils/executor/profiler_func 各 1 (b)；
trading_dates_mixin/logger 各 1 (c)；stock_position 1 (d)
```

**完整 61 行表**见 §4.1（`file / unit / cls / lenA/lenB / flags o·m·p / 首分歧`）。

**本批靶 jq 的两单元归属**：`b-orphan-child`，`reason = target instr same but len 352/348`
（`mcls=D-or-len`，长度差 4 = 被丢掉的 4 条指令）——
即 **b 类里「差表现为指令数少 4」的一个具体成因：CJB skip 分支丢条件操作数**。
它与 R74 已修的 `abs2_orphan_child_emit`（`and region.entry in _ft3_rr.blocks`，补孤儿子块发射）
**不同**：那个修「子块没发射」，这个修「子块发射了但前导操作数没进链」。

## 4.1 六十一行表

| # | file | unit | cls | lenA/lenB | o m p | 首分歧 |
|---:|---|---|---|---:|:---:|---|
| 1 | klinedata.pyc | \<module>.get_kline_by_count_new\ | a-shared-merge-absorbed | 586/586 | 0 1 4 | 320 POP_JUMP_FORWARD_IF_NONE to 380 -> 320 POP_JUMP_FORWARD_IF_NONE to 402 |
| 2 | klinedata.pyc | \<module>.get_multiminute_his_data\ | a-shared-merge-absorbed | 478/480 | 1 1 7 | 32 POP_JUMP_FORWARD_IF_FALSE to 926 -> 32 POP_JUMP_FORWARD_IF_FALSE to 930 |
| 3 | klinedata.pyc | \<module>.kline_datetime_list\ | b-orphan-child | 389/389 | 2 0 2 | 246 POP_JUMP_FORWARD_IF_TRUE to 310 -> 246 POP_JUMP_FORWARD_IF_TRUE to 774 |
| 4 | finance.pyc | \<module>.get_fields\ | a-shared-merge-absorbed | 157/157 | 1 2 1 | 36 JUMP_FORWARD to 90 -> 36 JUMP_FORWARD to 254 |
| 5 | handlers.pyc | \<module>.TWHThreadController._target\ | b-orphan-child | 191/189 | 3 0 4 | 12 POP_JUMP_FORWARD_IF_FALSE to 146 -> 12 POP_JUMP_FORWARD_IF_FALSE to 142 |
| 6 | jq_trans_module.pyc | \<module>.func_attribute_history_convert_code.replace_args\ | b-orphan-child | 352/348 | 1 0 3 | 134 JUMP_FORWARD to 258 -> 134 JUMP_FORWARD to 250 |
| 7 | jq_trans_module.pyc | \<module>.func_get_bars_convert_code.replace_args\ | b-orphan-child | 648/644 | 1 0 6 | 134 JUMP_FORWARD to 258 -> 134 JUMP_FORWARD to 250 |
| 8 | wizard_quant_api.pyc | \<module>.filter_desicion\ | a-shared-merge-absorbed | 178/180 | 0 19 28 | 324 POP_JUMP_FORWARD_IF_NONE to 330 -> 324 POP_JUMP_FORWARD_IF_NONE to 356 |
| 9 | wizard_quant_api.pyc | \<module>.get_DMI.calculate_di.<genexpr>\ | d-displacement | 62/48 | 0 0 0 | 8 FOR_ITER to 120 -> 8 FOR_ITER to 92 |
| 10 | wizard_quant_api.pyc | \<module>.get_DMI.calculate_di.<genexpr>\ | d-displacement | 62/48 | 0 0 0 | 8 FOR_ITER to 120 -> 8 FOR_ITER to 92 |
| 11 | cgroup_utils.pyc | \<module>.set_cgroup_config\ | b-orphan-child | 540/541 | 6 0 0 | 834 POP_JUMP_FORWARD_IF_FALSE to 1024 -> 834 POP_JUMP_FORWARD_IF_FALSE to 1026 |
| 12 | email_utils.pyc | \<module>.send_email\ | a-shared-merge-absorbed | 193/195 | 0 1 1 | 44 POP_JUMP_FORWARD_IF_FALSE to 206 -> 44 POP_JUMP_FORWARD_IF_FALSE to 332 |
| 13 | trade_info_utils.pyc | \<module>.trade_operation\ | a-shared-merge-absorbed | 303/303 | 3 2 3 | 186 POP_JUMP_FORWARD_IF_FALSE to 324 -> 186 POP_JUMP_FORWARD_IF_FALSE to 334 |
| 14 | trade_info_utils.pyc | \<module>.get_trade_status\ | a2-shared-tail-extpred | 153/153 | 0 0 1 | 138 FOR_ITER to 288 -> 138 FOR_ITER to 262 |
| 15 | api_base.pyc | \<module>.get_history_df\ | a-shared-merge-absorbed | 1739/1739 | 5 3 23 | 348 POP_JUMP_FORWARD_IF_TRUE to 398 -> 348 POP_JUMP_FORWARD_IF_TRUE to 630 |
| 16 | calexrights_func.pyc | \<module>.change_his_to_forward\ | a-shared-merge-absorbed | 386/387 | 0 1 1 | 326 FOR_ITER to 738 -> 326 FOR_ITER to 740 |
| 17 | real_quote.pyc | \<module>.RealQuoteData.get_real_minute_kline\ | a-shared-merge-absorbed | 250/253 | 0 2 3 | 28 POP_JUMP_FORWARD_IF_FALSE to 116 -> 28 POP_JUMP_FORWARD_IF_FALSE to 390 |
| 18 | real_quote.pyc | \<module>.RealQuoteData.get_tick_direction\ | a-shared-merge-absorbed | 258/259 | 1 1 2 | 8 POP_JUMP_FORWARD_IF_FALSE to 512 -> 8 POP_JUMP_FORWARD_IF_FALSE to 514 |
| 19 | calexrights_func.pyc | \<module>.change_his_to_forward\ | a-shared-merge-absorbed | 386/387 | 0 1 1 | 326 FOR_ITER to 738 -> 326 FOR_ITER to 740 |
| 20 | bar.pyc | \<module>.BarData._history_bars\ | a-shared-merge-absorbed | 59/59 | 0 1 1 | 50 POP_JUMP_FORWARD_IF_FALSE to 60 -> 50 POP_JUMP_FORWARD_IF_FALSE to 92 |
| 21 | executor.pyc | \<module>.Executor.check_before_trading\ | b-orphan-child | 242/242 | 1 0 1 | 32 POP_JUMP_FORWARD_IF_FALSE to 70 -> 32 POP_JUMP_FORWARD_IF_FALSE to 100 |
| 22 | strategy_universe.pyc | \<module>.StrategyUniverse._on_clear_de_listed\ | a-shared-merge-absorbed | 63/63 | 0 1 1 | 32 POP_JUMP_FORWARD_IF_FALSE to 48 -> 32 POP_JUMP_FORWARD_IF_FALSE to 58 |
| 23 | trading_dates_mixin.pyc | \<module>.TradingDatesMixin.trading_dates_reload\ | c-target-diff-instr | 22/20 | 0 0 0 | 4 POP_JUMP_FORWARD_IF_FALSE to 36 -> 4 POP_JUMP_FORWARD_IF_FALSE to 12 |
| 24 | history_api.pyc | \<module>.get_price\ | a-shared-merge-absorbed | 189/191 | 0 1 0 | 174 POP_JUMP_FORWARD_IF_NONE to 264 -> 174 POP_JUMP_FORWARD_IF_NONE to 378 |
| 25 | order_api.pyc | \<module>.base_order\ | a2-shared-tail-extpred | 178/178 | 0 0 1 | 270 POP_JUMP_FORWARD_IF_TRUE to 350 -> 270 POP_JUMP_FORWARD_IF_TRUE to 290 |
| 26 | order_api.pyc | \<module>.future_order\ | a-shared-merge-absorbed | 100/91 | 0 2 1 | 46 POP_JUMP_FORWARD_IF_FALSE to 92 -> 46 POP_JUMP_FORWARD_IF_FALSE to 178 |
| 27 | order_api.pyc | \<module>.option_order\ | a-shared-merge-absorbed | 82/72 | 2 2 1 | 62 POP_JUMP_FORWARD_IF_TRUE to 158 -> 62 POP_JUMP_FORWARD_IF_TRUE to 80 |
| 28 | strategy.pyc | \<module>.Strategy.tick_worker_thread\ | a-shared-merge-absorbed | 267/267 | 2 2 6 | 122 POP_JUMP_FORWARD_IF_TRUE to 156 -> 122 POP_JUMP_FORWARD_IF_TRUE to 282 |
| 29 | stock_position.pyc | \<module>.StockPosition.make_trade\ | d-displacement | 165/161 | 0 0 0 | 32 POP_JUMP_FORWARD_IF_FALSE to 220 -> 32 POP_JUMP_FORWARD_IF_FALSE to 212 |
| 30 | realtime_event_source.pyc | \<module>.RealtimeEventSource.clock_worker\ | a-shared-merge-absorbed | 1274/1281 | 6 11 16 | 1328 POP_JUMP_FORWARD_IF_FALSE to 2494 -> 1328 POP_JUMP_FORWARD_IF_FALSE to 2476 |
| 31 | matcher.pyc | \<module>.DefaultMatcher.match\ | a-shared-merge-absorbed | 712/712 | 0 10 16 | 380 POP_JUMP_FORWARD_IF_FALSE to 390 -> 380 POP_JUMP_FORWARD_IF_FALSE to 920 |
| 32 | __init__.pyc | \<module>.PluginRiskCalculation._on_publish_after_trading_end\ | b-orphan-child | 486/478 | 1 0 5 | 844 POP_JUMP_FORWARD_IF_FALSE to 916 -> 844 POP_JUMP_FORWARD_IF_FALSE to 900 |
| 33 | __init__.pyc | \<module>.PluginRiskCalculation._save_testds_to_csv\ | b-orphan-child | 74/71 | 1 0 0 | 26 LOAD_FAST self -> 26 LOAD_FAST self |
| 34 | trade_live_broker.pyc | \<module>.TradeLiveBroker.on_pre_before_trading_start\ | a-shared-merge-absorbed | 115/115 | 0 1 1 | 6 POP_JUMP_FORWARD_IF_FALSE to 34 -> 6 POP_JUMP_FORWARD_IF_FALSE to 42 |
| 35 | trade_live_broker.pyc | \<module>.TradeLiveBroker._process_order\ | a-shared-merge-absorbed | 452/392 | 0 2 2 | 22 POP_JUMP_FORWARD_IF_FALSE to 892 -> 22 POP_JUMP_FORWARD_IF_FALSE to 770 |
| 36 | trade_live_broker.pyc | \<module>.TradeLiveBroker._process_tick_order\ | c-target-diff-instr | 161/161 | 0 0 0 | 52 JUMP_BACKWARD to 38 -> 52 JUMP_BACKWARD to 32 |
| 37 | trade_live_broker.pyc | \<module>.TradeLiveBroker._process_cancel_order\ | a-shared-merge-absorbed | 293/295 | 0 1 2 | 22 POP_JUMP_FORWARD_IF_FALSE to 574 -> 22 POP_JUMP_FORWARD_IF_FALSE to 576 |
| 38 | trade_live_broker.pyc | \<module>.TradeLiveBroker._trade_status_handle\ | a2-shared-tail-extpred | 113/111 | 0 0 1 | 10 LOAD_GLOBAL NULL + get_trade_status -> 10 LOAD_FAST self |
| 39 | trade_live_broker.pyc | \<module>.TradeLiveBroker.etf_purchase_redemption\ | d-displacement | 378/368 | 0 0 0 | 118 POP_JUMP_FORWARD_IF_FALSE to 742 -> 118 POP_JUMP_FORWARD_IF_FALSE to 722 |
| 40 | trade_live_broker.pyc | \<module>.TradeLiveBroker.rzrq_credit_order\ | a2-shared-tail-extpred | 697/697 | 0 0 3 | 802 JUMP_FORWARD to 870 -> 802 JUMP_FORWARD to 860 |
| 41 | trade_live_broker.pyc | \<module>.TradeLiveBroker.ipo_stocks_order\ | a-shared-merge-absorbed | 1070/1069 | 0 5 23 | 814 FOR_ITER to 2136 -> 814 FOR_ITER to 2134 |
| 42 | trade_live_broker.pyc | \<module>.TradeLiveBroker.get_ipo_stocks\ | a-shared-merge-absorbed | 449/449 | 0 2 12 | 372 POP_JUMP_FORWARD_IF_TRUE to 410 -> 372 POP_JUMP_FORWARD_IF_TRUE to 346 |
| 43 | trade_live_broker.pyc | \<module>.TradeLiveBroker.on_order_response_list_handle\ | a-shared-merge-absorbed | 106/106 | 0 1 2 | 44 POP_JUMP_FORWARD_IF_NONE to 84 -> 44 POP_JUMP_FORWARD_IF_NONE to 206 |
| 44 | trade_live_broker.pyc | \<module>.TradeLiveBroker.on_trade_response_list_handle\ | a-shared-merge-absorbed | 106/106 | 0 1 2 | 44 POP_JUMP_FORWARD_IF_NONE to 84 -> 44 POP_JUMP_FORWARD_IF_NONE to 206 |
| 45 | profiler_func.pyc | \<module>.ProfilerTool.show_func\ | b-orphan-child | 299/241 | 1 0 2 | 404 LOAD_GLOBAL NULL + range -> 404 LOAD_FAST d |
| 46 | future_contract_info.pyc | \<module>.FutureInfoCache.check_user\ | a2-shared-tail-extpred | 148/153 | 0 0 3 | 134 POP_JUMP_FORWARD_IF_TRUE to 146 -> 134 POP_JUMP_FORWARD_IF_TRUE to 302 |
| 47 | future_contract_info.pyc | \<module>.FutureInfoCache.info_conbine\ | a2-shared-tail-extpred | 53/53 | 0 0 1 | 26 POP_JUMP_FORWARD_IF_TRUE to 38 -> 26 POP_JUMP_FORWARD_IF_TRUE to 46 |
| 48 | quotation.pyc | \<module>.change_his_to_forward\ | a-shared-merge-absorbed | 546/547 | 0 1 2 | 458 FOR_ITER to 1058 -> 458 FOR_ITER to 1060 |
| 49 | quote.pyc | \<module>.Quote.build_current_period_df\ | d-displacement | 117/108 | 0 0 0 | 4 POP_JUMP_FORWARD_IF_TRUE to 230 -> 4 POP_JUMP_FORWARD_IF_TRUE to 212 |
| 50 | quote.pyc | \<module>.Quote.load_bars_from_hundsun\ | a-shared-merge-absorbed | 476/482 | 0 4 3 | 96 POP_JUMP_FORWARD_IF_FALSE to 486 -> 96 POP_TOP  |
| 51 | quote.pyc | \<module>.Quote.change_his_to_forward\ | a-shared-merge-absorbed | 527/528 | 0 1 2 | 440 FOR_ITER to 1020 -> 440 FOR_ITER to 1022 |
| 52 | quote.pyc | \<module>.Quote.change_his_to_backward\ | a2-shared-tail-extpred | 357/357 | 0 0 3 | 424 POP_JUMP_FORWARD_IF_TRUE to 478 -> 424 POP_JUMP_FORWARD_IF_TRUE to 474 |
| 53 | quote.pyc | \<module>.Quote.get_price\ | c-target-diff-instr | 228/230 | 0 0 0 | 118 POP_JUMP_FORWARD_IF_NONE to 232 -> 118 LOAD_CONST None |
| 54 | quote.pyc | \<module>.Quote.get_real_from_zeromq\ | a-shared-merge-absorbed | 702/698 | 2 1 3 | 268 POP_JUMP_FORWARD_IF_FALSE to 288 -> 268 POP_JUMP_FORWARD_IF_FALSE to 1342 |
| 55 | quote.pyc | \<module>.Quote.run_individual_transform\ | a-shared-merge-absorbed | 363/272 | 1 1 0 | 174 LOAD_FAST self -> 174 LOAD_FAST self |
| 56 | quote.pyc | \<module>.Quote.get_individual_data\ | a-shared-merge-absorbed | 313/312 | 1 1 3 | 2 POP_JUMP_FORWARD_IF_FALSE to 622 -> 2 POP_JUMP_FORWARD_IF_FALSE to 620 |
| 57 | quote_handler.pyc | \<module>.get_kline_local\ | a-shared-merge-absorbed | 758/760 | 0 6 3 | 156 POP_JUMP_FORWARD_IF_FALSE to 170 -> 156 POP_JUMP_FORWARD_IF_FALSE to 1516 |
| 58 | load_daily.pyc | \<module>\ | a-shared-merge-absorbed | 912/912 | 0 1 3 | 1190 JUMP_FORWARD to 1202 -> 1190 JUMP_FORWARD to 1232 |
| 59 | logger.pyc | \<module>.SafeFileHandler.check_baseFilename\ | c-target-diff-instr | 30/30 | 0 0 0 | 26 POP_JUMP_FORWARD_IF_TRUE to 52 -> 26 POP_JUMP_FORWARD_IF_TRUE to 56 |
| 60 | ptradeAccount.pyc | \<module>.PtradeAccount.order_response_order_update\ | b-orphan-child | 98/97 | 2 0 1 | 168 JUMP_FORWARD to 192 -> 168 LOAD_CONST None |
| 61 | ptradeAccount.pyc | \<module>.PtradeAccount.trade_response_order_update\ | b-orphan-child | 117/116 | 2 0 0 | 206 JUMP_FORWARD to 230 -> 206 LOAD_CONST None |

---

## 5. 与 fix2 / fix3 的重叠面

| 批 | 范围 | 单元数 | 与 fix1 的交集 |
|---|---|---|---|
| fix2 | F-PAD 8 + F-POLARITY 1 + F-OTHER 1 | 10 | **0 单元**（家族不同；清单见 `dump/crosstab75_fix1.txt` 同源 diag1 crosstab） |
| fix3 | inside-try 9 单元（用户裁定） | 9 | **0 单元**：9 个 inside-try 单元 = F-ABSORB 7（`trade_info_utils.trade_operation`、`real_quote.get_real_minute_kline`、`finance.get_fields`、`cgroup_utils.set_cgroup_config`、`email_utils.send_email`、`strategy.tick_worker_thread`、`realtime_event_source.clock_worker`）+ F-PAD 2（`quote.run_tick_socket`、`flytools.modify_batcktes_info`），**都不含 jq** |
| 机制面 | — | — | fix1 改的是 `_cjb_skip_inline_if` 丢操作数；fix3 改 try 区域归约；fix2 改 pad/polarity。三者在同一文件不同锚点，但 fix1 的嫁接只在「有记录」时发生，而记录只在 fix1 自己的丢弃分支写入 ⇒ 不会替 fix2/fix3 的靶单元改变行为（161 份产物实测只有 jq 变，已证） |

---

## 6. `real_quote.get_tick_direction` 解剖（BRIEF §2.2，R74 拒收点）

- **R74 发生了什么**（diag1 Q3，`tick_direction75.md`）：`try7_3` 的 5 处编辑根本没碰该单元
  （读数与 landed 逐位相同 ⇒ 过 ADR-1 是「没改」）；`try7_9/try7_10d` 新增的 T7（`2b9410cc`）
  把 flag 链摆正成 `if A: P else: <flag链>; return redata` 并在链后重发 try ⇒
  `sdelta 184→4`、`hunks 12→5`，但**尾部共享 `return pd_dict` 没重新发射**，
  3 个归一化 hunk 全是这一件事的三个投影（`231/247 JUMP_FORWARD to 512` 被物化成
  `LOAD_CONST None; RETURN_VALUE`、`256 LOAD_FAST pd_dict` → `258 LOAD_CONST None`）
  ⇒ `hunks_norm 2→3` 触发 ADR-1 拒收。
- **本批怎么避免**：fix1 的三个锚点**没有一个落在该单元的路径上** —— 实测
  `real_quote` 的 `*OK.py` 在 head 与 jqop1 之间 **sha16 完全相同**，
  `nhunks` 读数 `landed 3 → jqop1 3`（`get_real_minute_kline` `6 → 6`），**hunks_norm 不升**。
- 因此本批无需为它做任何补发；R74 的处方（给 T7 补尾部共享块重发射）仍归 fix3/后续批。

---

## 7. 遗留缺陷（本批不修，交接）

**同族操作数丢弃仍未覆盖的一个形态**（`fix1/synth/neg75_jqcond2` 观察到，未入 synth 交付）：

```python
if a and b or c:      # 语句上下文
    total += 4
# head 与 jqop1 都产成 `if not (a and b): total += 4`  ← or c 操作数同样丢了
```

- 两臂产物**逐字节相同**且**都失败**（`neg75_jqcond2` 2/3）⇒ 不是本批引入，也不是本批能覆盖的路径；
- 说明 `_cjb_skip_inline_if` 不是唯一的操作数丢弃入口（该例未走 skip 分支）。
- **交接建议**：作为 fix2/后续批的候选（同一 `_build_boolop_expression` 家族，可用同一嫁接助手），
  最小复现已留 `fix1/synth/`（`neg75_jqcond2.py/.pyc` 与 `out/*`）。

---

## 8. 证据索引

```
specs/jqop1.json                 3 edits 源（+81 行）
FACTS.md                         本文
synth/build_synth.py             复现+负例构造与断言
synth/{repro75_jqcond,neg75_jqcond}.{py,pyc}
synth/out/{head,jqop1}_*.py      两臂产物
synth/out/synth.json             SYNTH PASS 四项断言
dump/gates75_fix1.txt            门禁全文读数（本批权威数字）
dump/g0audit.txt                 G0 12/12 逐条
dump/submech75.txt               71 单元 a–e 归属 TSV（diag1 副本）
dump/list_fail75.txt             34 pyc 缺陷名单（绝对路径）
dump/list_canary.txt             金丝雀 4 支
dump/strict_fail75_{head,jqop1}.json   strict 逐函数读数
dump/{ab75_*,fail75_*,canary_*}.jsonl（在 center/logs、center/dump）
scripts/mkspec_jqop.py           spec 生成（锚点 count==1 断言）
scripts/{g0audit.py,batt69.py}   自检与分片电池
scripts/{probe_units,probe_fixcheck,probe_chain572,probe_pbv,probe_cond,probe_jq_prod,anchors,run_arm}.py
dump/jq_diff75.txt  dump/jq_regions.txt   字节与区域原始读数
```
