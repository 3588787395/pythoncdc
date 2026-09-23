# Round 56 结果（OUTCOME）

**本轮发货判据：R56-A**（`core/cfg/region_analyzer.py :: _detect_boolop_conditional_chain` 内
`_sb_has_body` 门的 `POP_JUMP_FORWARD_IF_FALSE` 支，净核锚点 `24443-24464`，+94 行单 hunk；
文件 `1 691 897 → 1 699 508 B`，CRLF `27 179 → 27 273`，裸 LF 0，无 BOM，
sha256[:20] `b10ee76b55754f09e945 → ae6f21e5d22fd05112ba`）。
`region_ast_generator.py`（`2a2e5d81bea58afaee47`，Round 55 落地）与
`comprehension_generator.py`（`00903b60ef2411cb6b37`，Round 54 落地）本轮逐字节未动。

## 来源与独立复核

判据本体由本轮修复工程师交付（`rounds/round56/final_spec.json` == `final_hunk.txt`，
自报数字见下），**按项目规则其自报不得作为发货依据**：本记录全部数字为我在**当前核**
（已含 R54-COMP 与 R55-A）上重建臂 `D:/Temp/r54gate/mirr_m56a` 后独立跑出的门禁结果。
工程师报告并纠正了 Round 54 简报里我采纳的一处机制叙述错误：R53-A 的同运算段豁免当时
**确已成立**，被弹出的是体块 `258`，真正的否决点在 `[R54-03-sbhasbody-reject]`（块 0，
`stmt_offs=[42,58,114,156,160]`）——Round 54 记录的「检测器从 B 进入、R53-A 未触发」叙述作废。

## 靶与判据

靶：`site-packages/fly/common/market_time.pyc :: <module>.MarketTime.is_open`
（严格 `seq_len orig=67 decomp=69`，官方该文件 10/10 ⇒ 官方尺看不见此缺陷）。
真实源码形状 `if (A and B) or (C and D): <体>` 后随兄弟语句 `return False`，
四运算元块 `162/186/210/234`，体入口 `258`，汇合 `316`。

判据（识别条件→归约方式→AST 映射见 hunk 内中文注释块，含反向排除 A/B）：在
`POP_JUMP_FORWARD_IF_FALSE` 支保留原白名单测试，另或入 `_r54_mixed`，其成立要求
(1) 跳目标 `J` 以条件跳转收尾（`J` 是判定块，不是汇合/兄弟入口）；(2) 另一后继 `F` 同为判定块、
`T_F ≠ J` 且 `T_F` 在 `J` 之后；(3) `F` 的另一后继恰为 `J`（两运算段在此汇流）；
(4) `T_J ≠ T_F` 且 `T_J` 在 `T_F` 之后（即「跳过汇合点落到更远处」）；(5) `J` 的正常后继 `K`
亦短路与 `T_J` 相同（`J`、`K` 共享同一出口 ⇒ 同属一个运算段）。
归约依据：若 (1)-(5) 成立，按普通条件结构认领会使**父区域的 merge 落在其子 BoolOpRegion 的内部块**
（实测 `blk 210 owner=BoolOpRegion@186 role=NORMAL`、父 `merge=210`），违反「每块唯一归属」与
「父层只引用子区域入口」；`_r54_mixed` 为假时代码逐字回到原白名单测试 ⇒ 本 hunk 严格附加。

## 门禁（我独立复核）

- **G0** 16 靶逐函数：仅 `fly/common/market_time.pyc 9/10 → 10/10`（该文件双尺全清），
  合计 **`766/851 → 767/851`**；其余 15 靶逐字未变。
  两处 Round 54 硬否决复验为清除：`quotation.pyc 148/150`（缺陷集合仍为
  `change_his_to_forward`、`get_trend`）、`klinedata.pyc 56/63`（`_is_same_type_date` 未出现）。
- **电池** 39 例（`D:/Temp/r54diag/wit54/`）：当前核 `MISMATCH=15 MATCH=24` → 臂/落地后
  **`MISMATCH=9 MATCH=30`**，修复 `w54_02/15/16/17/18/24` 等，**broken=0**，
  臂的 9 项失败为落地态 15 项失败的真子集。
- **G4** 全量 544 路径 A/B（A 侧 = Round 55 落地态产物运行 `br2_g4_all.jsonl`）：
  `TALLY SAME=543 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，唯一移动文件即靶
  `fly/common/market_time.pyc`，`files fully matched 485 → 485`。
- **G4′** 因 MOVED 集合只含靶文件，逐码对象复核即 G0 该项：`is_open` `seq_len → ok`，`BROKEN=0`。
  另按作者点名的反例逐支核对产物与落地态**逐字节相同**：`IQEngine/core/bar.pyc`
  （合取 (5) 排除的 `(X and Y) or Z` 形状，strict 82/85 不变）、`klinedata`、`quotation`、
  `trade_live_broker`。
- **G5** 落地核重跑：`market_time` 产物与门禁臂**逐字节相同**；39 例电池 `30 MATCH`；
  金丝雀 `fly/data/quotation.pyc` 官方 `143/143`、严格 `148/150` 逐字不变；
  `test_repros/round16_sink` 15/15 MATCH。
- **G6** `batch --index pyc_index.json --all --round 56` → **402 verified / 0 failed**
  （`ok_pyc 375 / partial_pyc 27 / failed_pyc 0`），全量重跑仅 1 支 `*OK.py` 变化（靶文件，工具生成）。
- **G7**（`stats` 原样）：`total_functions 5746`、`matched_functions 5669`、
  `cumulative_match_rate 98.66%` —— **本轮官方尺继续零位移**（该缺陷为长度型 `seq_len`，
  但 `market_time` 官方计数早已 10/10，说明官方尺以跳转/噪声容忍判定，同样看不见它），
  收益在严格尺 `+1` 函数并使 `market_time.pyc` 成为双尺全清文件。
  `pyc_index.json` 非轮次戳变化行数 0。

## 遗留与移交（Round 57）

1. 电池 9 项仍失败：`w54_21/w54_22` 需要**统一阶段的三元 3 操作元链截断**（另一族）；
   其余为 Round 54/55 已入册形状。作者另测得「去掉合取 (5) 的 i1 变体会重新破坏
   `IQEngine/core/bar._history_bars`（58/58 → 57/58，凭空造出 `if not (X and Y)`）」
   ⇒ 合取 (5) 是承重条件，不得为扩大命中而删。
2. 入库未发的三元 kwarg 候选（Round 55 OUTCOME 第 1 条，两枚 spec 已归档）语料零触发，
   续做前须先解释「为何 `w16` 复刻可修而真实 `future_order` 不动」。
3. 未收口：`base_order [target_diff] #136`、线 B 伪造尾随 `continue`
   （`trade_live_broker :: _on_set_positions 297/298`、`finance :: func_get_fundamentals_daily_data 192/193`）、
   三大损失 `DefaultLogger.setup -65`、`get_kline_local -78`、`get_TradeMode_trades -90`。
4. 全量现状：`stats` 5669/5746（98.66%），27 支 partial 文件、77 支函数官方不匹配；
   严格尺另余 `117 - (本轮及 Round 54/55 已修 6+6+1) = 104` 项缺陷待分族。

## 归档

`rounds/round56/`：本文件 + 判据 spec/hunk + 臂构建与门禁脚本（`land55.py`、`g054base.py`、
`runw.py`、`g4p55.py`）+ G0（`g056_a/b.log`）+ G4（`m56_g4_all.jsonl` 与 24 分片日志、
A 侧 `br2_g4_all.jsonl`）+ G5/G6/G7 日志 + 修复工程师自报物证（`final_spec.json`、
`final_hunk.txt`、`spec_i3.json`、其 `mirr_*`/`log_*` 索引）。起始 HEAD `e8bb2cc0`
（Round 55 记录），落地前 `git status --porcelain core/ pycdc.py` 为空。
