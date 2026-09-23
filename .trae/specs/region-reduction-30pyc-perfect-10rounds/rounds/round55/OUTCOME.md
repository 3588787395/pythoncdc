# Round 55 结果（OUTCOME）

**本轮发货判据：R55-A**（`core/cfg/region_ast_generator.py :: _generate_block_statements`，
锚点在净核 `42113` 的 `stmts = self._generate_block_statements_body(...)` /
`self._mark_with_exit_return_explicit(...)` / `return stmts` 之后，+41 行单 hunk；
文件 `3 011 895 → 3 015 091 B`，CRLF `48 777 → 48 816`，裸 LF 0，BOM 保留，
sha256[:20] `c36cf1fe7dad68377c80 → 2a2e5d81bea58afaee47`）。
`region_analyzer.py`（`b10ee76b55754f09e945`）与 `comprehension_generator.py`
（`00903b60ef2411cb6b37`，Round 54 落地）本轮逐字节未动。

## 靶与真实根因

靶族：`api_get_from_zeromq` 四胞胎与同形的 `try/except` 尾块——缺陷类型是**严格 `target_diff`
（长度相同、跳转终点错位）**，官方尺按索引对齐看不见，因此本轮是一次「官方零位移、严格 +6」的
发货（与 Round 53 同类，判据与门禁逐项留档）。

`dis` 取证（`D:/Temp/r54ddiag/gt_*.txt`）：CPython 3.11 把循环内 `break` 编成
「跳向循环出口的中转块」，该中转块只含一条无条件跳转、被 break 独占。发射端在
try 体（或臂）收尾处没有补 `Break`，于是本块正常流顺着中转块之后的代码继续跑，
重编译后长度不变而跳转终点错位。

## 判据（只用块角色 / 后继集合 / 认领状态）

识别条件：① 本块处在循环体内（`self._current_loop` 非空）；② 已发射语句末尾不是
Break/Return/Raise/Continue；③ 本块的**正常**后继（剔除异常表隐式边）恰好只有一个；
④ 该后继是纯跳转块（块内只有 JUMP_FORWARD/JUMP_ABSOLUTE 与 EXTENDED_ARG/NOP/CACHE/POP_BLOCK
噪声）且末指令是前向无条件跳转；⑤ 其块角色属 `BlockRole.BREAK / PURE_BREAK`；
⑥ 它尚未被任何区域认领；⑦ **它的唯一前驱就是本块**。
归约方式：把该中转块判为本块收尾语句消费掉（并入 `generated_blocks` / `generated_offsets`），
不再作为独立语句发射。AST 映射：`stmts += [Break]`，中转块由 break 语句重编译自然再生。

 conjunct ⑦ 是实测反例逼出来的：`fly/common/flytools.pyc :: get_host_mem` 的 break 属于
外层 `if 'Mem' in ...` 体，其中转块同时被内层 if 的假路落入（前驱 ≥2）；加上 ⑦ 之前
G4′ 报 `FIXED=6 BROKEN=1`，加上之后 `FIXED=6 BROKEN=0`，电池 14 MATCH 未减。

## 门禁

- **电池** 17 例（`D:/Temp/r54ddiag/wit54/`，含 `r54_14/15/16/17` 等阴性对照）：
  落地核 `MISMATCH=8 MATCH=9` → 臂/落地后 **`MISMATCH=3 MATCH=14`**，对照全部未破，
  余 3 例属另一族（见移交）。
- **G0** 16 靶逐函数严格合计 **`762/851 → 766/851`**（`quote 72→74`、`real_quote 39→40`、
  `main 28→29`），其余 13 靶逐字未变（含金丝雀 `quotation 148/150`、`klinedata 56/63`、
  Round 54 的 `quote_handler 67/72`）。
- **G4** 全量 544 路径 A/B（A 侧 = 当前落地核产物 `cmp_g4_all.jsonl`）：
  `TALLY SAME=535 IMPROVED=0 REGRESSION=0 MOVED=9 ERR=0`，`files fully matched 485 → 485`。
- **G4′** 9 支 MOVED 全部逐码对象严格复核（`g4p55.py`）：**`FIXED=6 BROKEN=0 CHANGED=0`** ——
  6 处修复为 `quote :: Quote.api_get_from_zeromq / api_get_from_multi_zeromq`、
  `real_quote :: RealQuoteData.api_get_from_zeromq`、`main :: api_get_from_zeromq`、
  `fly/common/common :: api_get_from_zeromq`、`fly/dumpload/load_daily :: api_get_from_zeromq`；
  其余 3 支移动（`fileio_utils`、`realtime_event_source`、`r31a_witness`）经产物 diff 与严格
  双尺核对，均为 `try: ... else: break` → `try: ... break` 的**字节码等价**改写
  （严格 ok→ok、缺陷集合逐字不变），非新缺陷也非新修复。
- **G5** 落地核重跑：8 支受影响 pyc 产物与门禁臂产物 **8/8 逐字节相同**；
  金丝雀 `fly/data/quotation.pyc` 官方 `143/143`、严格 `148/150`
  （缺陷集合逐字相同：`change_his_to_forward`、`get_trend`）；`test_repros/round16_sink`
  15/15 MATCH（第 16 项 `run_all.py` 为驱动脚本）。
- **G6** `batch --index pyc_index.json --all --round 55` → **402 verified / 0 failed**
  （`ok_pyc 375 / partial_pyc 27 / failed_pyc 0`），全量重跑仅 8 支 `*OK.py` 变化
  ＝ G4 的 MOVED 集合（site-packages 内 8 支；`r31a_witness` 不在索引），无手改产物。
- **G7**（`stats` 原样）：`total_functions 5746`（分母未动）、`matched_functions 5669`、
  `cumulative_match_rate 98.66%` —— **与 Round 54 相同：本轮官方尺零位移**，收益全在严格尺
  （+6 函数）。`pyc_index.json` 非轮次戳变化行数 = 0，仍纯 CRLF 4553 行、裸 LF 0。

## 否证、入库与移交（Round 56）

1. **入库的三元 kwarg 线（不发）**：`D:/Temp/r55diag/spec_r55a.json`（KW_NAMES→首个 CALL 绑定 +
   callee 前缀回收 + 尾随 CALL 包裹）与 `spec_r55b.json`（按操作数栈序通用装配）经实测
   对 33 例 `wit54c` 电池把 `12 MATCH → 16 MATCH`（含把真实 `future_order` 形 `w16` 修到逐字节 ok），
   但 **G0 16 靶与四支相关 pyc 产物全部与落地态逐字节相同** ⇒ 零语料收益，按「每轮至少解决一支
   pyc」不得单独发货。其根因贡献已入册：`region_ast_generator.py:41544-41548` 绑定块内最后一个
   CALL 是错的（P1），以及 `41623-41628` 的关键字槽位在 `len(kw_names) > 三元数` 时静默
   `return None`（真实形状是位置/关键字实参**交错**：`.format(i=a, s=b, side=<t1>, oper=<t2>, sh=e, h=<t3>)`）。
   Round 56 若续此线，须先解释「为何语料不触发」——`w16` 的复刻与真实 `future_order` 之间仍有
   未被本判据覆盖的前置差异（Round 50 的 `[R54C2 GATE] PRED_CALL_CHAIN` 站点是最可能入口）。
2. **Round 56 主靶（已取证、待复核）**：线 A 的 `market_time :: is_open` 修复由修复工程师交付为
   `D:/Temp/r54impl/final_spec.json`（`_detect_boolop_conditional_chain` 净核 `24443-24464`，
   `_sb_has_body` 门内 `POP_JUMP_IF_FALSE` 支，+94 行；五个合取 (1)-(5) 以「短路边落在下一
   运算段入口」为凭据），自报：其 `mirr_head` 复现落地 760/851、臂 **763/851** 零回归；
   电池 39 例 `24 → 30 MATCH`、broken 0；两处硬否决（`quotation`、`klinedata`）已清除，
   且新反例 `IQEngine/core/bar._history_bars` 由合取 (5) 排除（产物逐字节同）；
   作用面用探针穷举 549 支 pyc：仅 12 站点 / 5 模块开火，只有 `market_time`、`quote_handler` 产物移动。
   **其自报数字须由门禁独立复核后方可落地**；其并我的 R54-COMP/R55-A 已改动的核存在叠加关系，
   须在最新核上重建臂再跑 G0/G4/G4′。
3. **同族残留**：`r54_03/05/09` 三例（本轮电池仍 MISMATCH）需要 unify 阶段的「三元操作元为
   3 项链」截断处理，属另一族；`order_api :: base_order [target_diff] #136` 已证明与三元 kwarg
   不同族（0 丢 0 增，仅跳转终点 1124→926）。
4. 未收口旁支：线 B（伪造尾随 `continue`，`_on_set_positions 297/298`、
   `finance :: func_get_fundamentals_daily_data 192/193`）诊断代理耗尽轮次未出结论，
   其三枚草图 spec 已入库；`DefaultLogger.setup -65`、`get_kline_local -78`、
   `get_TradeMode_trades -90` 三大损失归属见 Round 54 OUTCOME 第 3 条。

## 归档

`rounds/round55/`：本文件 + `wit54d/` 17 支电池 + `spec_r55break.json`/`mk55br.py`（含 ⑦ 合取）
+ `land55.py`/`g4p55.py`/`runw.py` + G0（`g055br_a/b.log`、`g054base.log`）
+ G4（`br_g4_all.jsonl`、`br2_g4_all.jsonl` 与分片日志）+ G4′/G5/G6/G7 日志
+ 入库三元线（`spec_r55a.json`、`spec_r55b.json`、`mkdiag55*.py`、`spec_diag55*.json`）
+ 线 A 修复工程师交付（`final_spec.json`、`final_hunk.txt` 及自报日志）。起始 HEAD `a0379e63`
（Round 54 记录），落地前 `git status --porcelain core/ pycdc.py` 为空。
