# Round 2 主代理验证序（VERIFICATION）

轮次：rr-v3r02 · Task 3（双单元损失族）+ Round 1 移交残项
封表时点：2026-10-06
before（判据唯一口径）= `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after = `rounds/round2/after/shard*_report.json`（402 产物在本轮终态代码上先删后重生成，8 片 regen failed 合计 0）
ruler `pylingual/equivalence_check.py` sha `9c7567bd6776b36b`、interp 3.11.7

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 batch + compare（对基线） | units 6554→**6566/6617（99.2293%）**、files 369→**377/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 同读数对 Round 1 终态（`rounds/round1/after3`） | units 6564→6566、files 376→377 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓（增量核对，防止轮内自欺） |
| 2 | quotation 单验 | **152/153**，失败单元仍 `<module>.get_fundflow_day` | 零新增失败；B102 替换形态未回退 ✓ |
| 3 | tests 六套件 | **277 passed / 2 failed / 2 xpassed**（test_B01 + test_BOUNDARY_02） | 零新增失败 ✓ |
| 4 | IV.2 门禁自检 | IMPORT_OK、compileall rc=0、禁止前缀新增方法 **0**、调试残留 **0**、硬编码上限 **0**、`region_ast_generator.py` 全 CRLF 单头 BOM、`region_analyzer.py` 本批逐字节未动 | 全过 ✓ |
| 5 | 电池（主代理独立复算，不引用工程师自报） | `r2v3_probe_index.json` 62 臂 **105/126 units、41 success / 21 failure**（起点 85/114→90→95→105）；`r1_probe_index` **108/110**；`r1_regress_index` **34/34** | 本轮新增 6 条永久臂（b20/b21/b22-b25）全绿；零臂由绿转红 ✓ |

## II. 本轮三个修复批次（每批一个家族，串行派发）

| 批次 | 家族 | 落地标记 | 电池/语料净效应 | 是否闭环 |
|------|------|----------|-----------------|----------|
| B108 | 混合极性 `A or not B` 链被整体否定为 `not (A or B)` | `[R2-B108 …]`（region_ast_generator，5 处） | c 族 8 臂翻转 5；`future_contract_info` 27/29→**28/29** | 未闭环：c06/check_user＝finally 释放块复制；c11＝嵌套 if 折叠 `_all_negated`；c12＝`region_analyzer.py:29105` op_type 误标 |
| B106 | 处理器尾 `POP_EXCEPT + JUMP_BACKWARD→循环条件入口` 被降级为 `JUMP_FORWARD→try 尾` | `[R2-B106 …]`（4 处，新增 `_except_tail_backedge_is_loop_continue`） | b07 转绿＋b20/b21 永久臂；`risk_calculation` 仍 41/43 | 未闭环：残余第二分歧分属 B107/他族 |
| B107 | `_process_if_blocks` 从不为 `LoopRegion` 入口派发抽象节点 ⇒ 臂内 while 被重建为顺序块 | `[R2-B107 …]`（7 处，新增 `_arm_loop_child_entry` 等 3 个谓词） | b02/b05 转绿＋b22-b25；`fly/logger.pyc` 63/64→**64/64（本轮转完全 OK 的 pyc）** | 未闭环：b01（循环体内 `from mod import X` 重建，独立缺陷）、b03（merge 归属另一侧）、b12-b15 经核对该签名不符 |

三批均经主代理复核：标记命中数实测（5/4/7）、引用符号 grep 存在、读数由我方 `pyc_verify` 复算而非引用自报。

## III. 轮门禁判定

- ≥1 个 pyc 由 failure 转 success：**1 个**（`fly/logger.pyc` 64/64，同目录 `+OK.py` 由 pycdc 重生成、全单元 Equal）✓
- 全量单元读数净增：6564 → 6566（+2；对基线 +12）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`（对基线与对轮内前态双重核对）✓
- 产物零手改（一律先删后重生成，402/402 重生成 0 失败）✓；单条命令 ≤300s（regen 每命令 ≤3 片、verify 每命令 ≤4 片）✓；派发前本地提交 ✓
- push：本轮 3 个提交已推 `origin/rr-v3-full-corpus`（`37b3a4d0..bd12153b`），非 `main`——F: 本地 main 已推进至 `1aecc150`（rr-v2r03 round3），推 main 会令用户本地线与 origin/main 分叉
- **Round 2 判定：通过，可开启 Round 3**

## IV. 语料残局（本轮封表时点，25 文件 / 51 单元；48 条 Different control flow + 3 条 Different bytecode）

| 文件 | units | 损失 |
|------|-------|------|
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | -10 |
| fly/data/quote.pyc | 85/92 | -7 |
| IQCommon/util/trade_info_utils.pyc | 37/41 | -4 |
| IQCommon/api/klinedata.pyc | 61/64 | -3 |
| IQCommon/strategy/wizard_quant_api.pyc | 55/58 | -3 |
| IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc | 34/37 | -3 |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | 43/45 | -2 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | -2 |
| IQCommon/data/finance.pyc | 31/32 | -1 |
| IQCommon/logger/handlers.pyc | 29/30 | -1 |
| IQData/api/api_base.pyc | 27/28 | -1 |
| IQEngine/core/bar.pyc | 84/85 | -1 |
| IQEngine/core/strategy/strategy_universe.pyc | 10/11 | -1 |
| IQEngine/data/trading_dates_mixin.pyc | 13/14 | -1 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 26/27 | -1 |
| IQEngine/plugins/plugin_system_accounts/position_model/stock_position.pyc | 36/37 | -1 |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | 12/13 | -1 |
| IQEngine/plugins/plugin_system_matcher/matcher.pyc | 16/17 | -1 |
| IQEngine/plugins/plugin_system_trade/function.pyc | 70/71 | -1 |
| IQEngine/utils/profiler_func.pyc | 17/18 | -1 |
| fly/common/flytools.pyc | 65/66 | -1 |
| fly/common/future_contract_info.pyc | 28/29 | -1 |
| fly/data/quotation.pyc | 152/153 | -1 |
| fly/data/quote_handler.pyc | 78/79 | -1 |
| fly/dumpload/load_daily.pyc | 26/27 | -1 |

## V. 移交清单（未闭环项逐条实名，不以读数掩盖）

- **B99** 仍未闭（`IQCommon/logger/handlers._target` 双 sink 归并；B107 报告确认 `r2v3_b14` 第一分歧即此形，未被冒领）
- **B104** a 族 7 臂（链汇合块为终止 `return` 时 clause (4) 的 E 箱空豁免让 merge 交给链构造器，取到跨区边进入的块）
- **B105** `get_real_minute_kline`（`_flip_is_none_compare`）——测试工程师如实标注**无最小合成孪生标本**
- **B106 残** b09/b18（break sink 复制）、b10/b11（try 未被交付为 TryRegion，TE 站点零命中）
- **B107 残** b01（循环体内 `from mod import X` 被重建为 `X = (…)`，顶层已可复现＝独立缺陷）、b03（merge 块归属另一侧）、b12/b13/b15（签名不符，未认领）
- **B108 残** c06（finally 释放块复制）、c11（嵌套 if 折叠闩锁）、c12（`op_type` 误标）
- **B101** 合成线索（语料无实例，禁止据此改判据）；**B102** quotation 单元替换
- 本轮 3 批为「部分封闭」：家族判据面已扩，但除 `fly/logger.pyc` 外未有整文件转绿——如实记为未闭环，不得以电池单元增量冒充文件级 100%
