# Round 5 · FIX_A_FAMILY —— A 族（臂出口 / 成员边汇合身份）：共享目标的 S-vs-F 判别式

轮次：Round 5 / 簇 = `rounds/round4/REVIEW.md` §6 的 A 族（B100 / B104 / B110 同判据轴，7 个语料文件）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；ruler sha `9c7567bd6776b36b`、interp 3.11.7 64 位）。
落地文件：**`core/cfg/region_analyzer.py` 单文件**（`region_ast_generator.py` / `code_generator.py` 零改动）。

**结论标记：「代码已落地」**。翻转计数：**语料文件 0 个 / r4 合成臂 1 条**
（`r4v3_a05_for_host` 的 `<module>.f` 由 MISMATCH→MATCH，臂读数 1/2→2/2、文件 failure→success），
**零条绿臂转红、零 pin 下跌**（§5 全部读数逐位复核）。

---

## 1. 概念问题与判别式（S-vs-F）

一条 or-run 在跳转语境里被 CPython 编成「每名成员块尾一条正向条件跳边指向**同一个** T，
落空边接下一成员」。只读 opcode 形状时两种意义完全同形：

* (i) **T 是该 run 的假出口 / 本层汇合块** —— 源文 `if not (A or B ...)`，成员 TRUE 边就是
  「跳过臂体」的出口，消费端 R14c 的整链取反 `not (A or B)` 正确；
* (ii) **T 是该 run 的真入口（臂体首块）** —— 源文 `if A or B`，成员 TRUE 边进入臂体、落空侧才是
  假出口；此时取反会互换两臂入口并丢掉臂体（`elif_conditions [512]→[512,612]`、臂体 preds `3→1` 那一族）。

判别式（`_boolop_shared_target_is_join`，只用白名单结构事实）：
**T 是否被「链外同层块」认领为出口。** 若存在非成员前驱 P 以**无条件跳边**
（`JUMP_FORWARD`/`JUMP_BACKWARD`，argval == T）或**自然直落**（P 块末非跳转且 T 是 P 的正常后继）
进入 T ⇒ P 是兄弟臂尾、T 是本层汇合块 ⇒ 情形 (i)，放行成员对；
若 T 的全部入边都是**条件测试边**（成员自身或同一 run 的续接腿）⇒ T 只被"测进"而不被"跳进" ⇒ 情形 (ii)，
维持原拒绝。**不看** depth、宿主类型、成员数、操作数类型，也不向祖先区域的成员关系取证
（承 `[r1-b98-elsescope]`），也不以后继穷尽当终态证据（承 `[r3-b103-armjoin-termexit]`）。

站点（实测行号，grep 核实）：`region_analyzer.py:29567` 是链 walk 唯一把该成员对交予
`_b1b_loop_body_run_continuation` 的地方；原函数体末行（入轮 30318）对「同为 TRUE 族」一律 `return False`，
docstring 自陈「纯 or 链在循环体内仍走既有 IfRegion or 链路径」——本轮实测该前提**不成立**
（line-trace：`_detect_boolop_conditional_chain(136)` 的失败返回点即 29774，路径 29560→29570 `break`）。
故改动落在同一函数的 TRUE/TRUE 分支 + 新判别式方法，**单文件**即闭合，无需生成端补丁：
R14c 闩锁（`region_ast_generator.py:23862-23895`）本就按「全员 IF_TRUE 同目标 ⇒ 负极性整链」处理，
它此前拿不到完整 `op_chain`。

## 2. 逐文件 前驱 / 目标 与 产物 before→after（实测原文）

| 靶 | 成员 → 共享目标 T | T 的前驱（实测） | 判别 | before → after |
|---|---|---|---|---|
| `r4v3_a07_no_or_control` `<module>.f` | 136, 148 均 `POP_JUMP_FORWARD_IF_TRUE → off350` | `[1,3,4,5,10,15,17,19,20]`，其中 3/10/15/17/19/20 为兄弟臂尾无条件跳入 | **True**（T=本层汇合块） | 产物 `elif dt_strf > '15:15:00' or dt_strf < '08:30:00':`（无 `not`，链未建、块 148 无主）→ `elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):`（BoolOpRegion[136,148]、merge=off350、块 148 归位）；读数仍 1/2（残根 = 臂体尾被 `break` 外提、`sleep(60)` 材料化到循环之后） |
| `r4v3_a05_for_host` `<module>.f` | 142, 154 → off416 | `[8,142,154,370,386]`，370/386 为非成员臂尾 | **True** | 1/2 Different control flow → **2/2 MATCH（翻转）**；产物 `elif not (… or …):` + 臂内 if/elif 完整、`continue` 归位 |
| `r4v3_a02 / a06 / a08 / a09 / a13`（while 宿主同形） | 136, 148 → off316 / off332 / off254 / off298 等 | 均含 ≥1 非成员无条件入边 | **True ×1 各** | 取反与链完整性同 a07 复原；读数仍各 1/2（同一残根） |
| `r4v3_a03_no_loop_host`（if 宿主） | — | 链 walk 未走到本守卫（该守卫只在候选块被 **LoopRegion** 认领时触发） | calls=0 | 逐位不变（1/2） |
| `r4v3_a14_min_arm` | — | — | calls=0 | 不变（2/3） |
| `r4v3_a15_shared_target_is_merge`（新臂 (i)） | 94, 106 → off192 | `[94,106,162]`，162 无条件入边 | **True** | 新建即 **2/2 MATCH** |
| `r4v3_a17_shared_target_is_merge_three`（新臂 (i)·三名成员） | 110,122→off198；122,134→off198 | `[34,78,110,122,134,146]`，34/78/146 兄弟臂尾 | **True ×2** | 新建即 **2/2 MATCH** |
| `r4v3_a16_shared_target_is_true_entry`（新臂 (ii)） | `if A or B: sleep(60)` 真入口形 | 守卫未被触发（成员对不进 LoopRegion 认领分支） | calls=0 | 新建即 **2/2 MATCH**（正极性未被触碰） |
| 语料 `strategy / api_base / matcher / finance / bar / function` | — | 链 walk 在到达本守卫前即被其它条件截断（**calls=0**） | 无命中 | 读数逐位不变：26/27 · 27/28 · 16/17 · 31/32 · 84/85 · 70/71 |
| 语料 `fly/dumpload/load_daily` `<module>` | 1 次调用 | 目标只被测试边进入 | **False**（保守弃权） | 不变 26/27 |

## 3. 标记、True-hits 与 flips

| 标记 | 站点（当前字节行） | 命中实测 | 造成的翻转 |
|---|---|---|---|
| `[R5-B100-armjoin-trueentry]` ×4（TRUE/TRUE 分支注释 / 新方法 docstring / `_b1b_loop_body_run_continuation` 更正段 / 同方法六项补块） | `region_analyzer.py` `_b1b_loop_body_run_continuation` 的 TRUE/TRUE 分支 + 新方法 `_boolop_shared_target_is_join` | 入轮 34 臂 + 7 语料全量重跑：**8 次调用 / 7 次判真**（a02 a05 a06 a07 a08 a09 a13 各 1；语料仅 load_daily 1 次且判 False）；3 条新臂再贡献 **3 次调用 / 3 次判真** | **1 单元 + 1 文件**（`r4v3_a05_for_host`）；其余 6 次判真改了区域事实（链完整、取反正确）但被 §2 所列残根挡住，**如实登记为命中未翻转** |

必须存活的原标记复验（全库计数）：`[R2-B106` 4、`[R2-B107` 7、`[R2-B108` 5、`[R3-B115` 1、
`[R3-B109` 3、`[R4-B116 sinkexit]` 4 —— 逐条与入轮相同。

## 4. 五套电池 + 13 pin + pytest（全部为本票代码态实测原文；语料/臂产物一律先删后 `pycdc.py` 重生成，无手改）

```
batch round4/r4_probe_index（本轮追加 3 条臂后 37 臂 / 81 单元）
      71/81 单元  files 27 success / 10 failure / compile_error 0 / error 0
      同一批在未追加前的入轮 34 臂子集读数：65/75 单元、24 success / 10 failure
      （入轮基线 64/75、23/11 ⇒ +1 单元 +1 文件，零条绿臂转红）
batch round1/r1_probe_index     108/110 单元  files 44 / 2      （STAY，产物已重生成）
batch round1/r1_regress_index    34/34  单元  files 17 / 0      （STAY，产物已重生成）
batch round2/r2v3_probe_index   105/126 单元  files 41 / 21     （STAY，产物已重生成）
batch round3/r3_probe_index     101/122 单元  files 35 / 21     （STAY，产物已重生成）
pins（13 文件，先删后重生成再判）
      fly/data/quotation.pyc                152/153  失败单元仍 <module>.get_fundflow_day
      IQCommon/logger/handlers.pyc           29/30   失败单元仍 <module>.TWHThreadController._target
      IQEngine/data/trading_dates_mixin.pyc  14/14   success
      …/position_model/stock_position.pyc    37/37   success
      IQCommon/util/cgroup_utils.pyc          8/8 · IQCommon/util/email_utils.pyc 4/4
      IQData/utils/calexrights_func.pyc       8/8 · fly/common/future_contract_info.pyc 29/29
      fly/logger.pyc 64/64 · fly/simtradding/ptradeAccount.pyc 137/137
      fly/data/quote.pyc 86/92 · IQCommon/util/trade_info_utils.pyc 37/41
      IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc 118/128
      （13 条全部 = 基线，无一下跌）
pytest 6 套件        2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、
                     test_BOUNDARY_02_large_function）
import 三模块 OK；python -X utf8 -m compileall -q core OK
```

语料 7 靶（strategy / api_base / matcher / finance / bar / function / load_daily）在本轮代码态重生成后
合计 **280/287 单元**，与入轮逐位相同 ⇒ **语料侧 0 翻转**。

## 5. 未闭残余（下一手最窄表述，实测支撑）

1. **命中未翻转的 6 条臂同卡一处**：链完整 + 取反正确之后，`while` 宿主的臂尾仍被外提成
   `break` + 循环后语句段（a07 实测 `if chained: break … sleep(60); sleep(60)`）。
   该根在**臂尾出口的交付**，不在成员认领：与 Round-4 B117（出口边被内吞）方向相反。
2. **语料 6 靶 calls=0**：`strategy`/`api_base`/`matcher`/`finance`/`bar`/`function` 的 or-run 成员对
   根本没走到 LoopRegion 认领守卫（成员块未被循环体认领，或链 walk 在更早的
   `ft_succ`/R38/`_equivalent_exits` 分支即 break）。⇒ A 族语料的下一站点仍在
   `_detect_boolop_conditional_chain` 的 walk 侧（链式比较续腿的认领，`FIX_ELIF_HOST.md` §7.1 配方），
   不是本守卫。
3. **情形 (ii) 的正向判据仍缺证据**：新臂 a16 走的是既有路径（calls=0），
   本轮未获得「同一 run 的真入口被判 False」的实弹样本；语料侧唯一一次判 False（load_daily）
   未改变任何区域事实。真入口一侧的**主动**判别（抑制取反并把 T 认作臂体入口）尚未落地，
   也不得凭空 bolt-on（`FIX_JOIN_IDENTITY.md` §2.2 已实测该形 4 命中 0 翻转）。

## 6. 字节完整性核验（本轮改动后）

```
core/cfg/region_analyzer.py      2037812 → 2045409 bytes；32073 → 32168 行；
                                 前导 BOM 恰好 1；CRLF 32167；bare LF 0；ast.parse OK
core/cfg/region_ast_generator.py 3684310 bytes / 58669 行 / 1 BOM / CRLF 58668 —— 逐字节未动
core/cfg/code_generator.py       未触碰（无 BOM）
```

改动方法清单：`_b1b_loop_body_run_continuation`（TRUE/TRUE 分支 + docstring 更正段 + 六项 ①-⑥ 与
C1/C2/C3 补块）、`_boolop_shared_target_is_join`（新增，六项 ①-⑥ + C1/C2/C3 齐备）。
终态复判：r4 索引 37 臂在**最终字节态**上重生成后复跑 = 71/81 单元、27 success / 10 failure
（与 §4 记录逐位相同；文档补写仅动 docstring，行为不变）。
禁止前缀命名（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）新增方法 **0**；
硬编码深度/数量/操作数上限 **0**；文件名·函数名·偏移特判 **0**；文本后处理 **0**；调试残留 **0**。
