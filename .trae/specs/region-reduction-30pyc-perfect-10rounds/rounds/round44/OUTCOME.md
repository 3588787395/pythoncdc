# Round 44 结果：落地 R44-A + R44-B（守卫块不得并入 LoopRegion ∧ 纯条件回边块无语句可发射）

落地铁笔：本轮 `core/` 改动为两文件两处插入，与实测镜像臂 `D:/Temp/r43gate/mirr_r44p12` 逐字节相同。

- `core/cfg/region_analyzer.py`：`a66248d3b9a3e0a1545e` → `55a9f61b9b0703063d44`，len 1 681 035，CRLF 27 023、裸 LF 0
- `core/cfg/region_ast_generator.py`：`11e2c67e2d7681735f9d` → `d4c430303a5d2b63753d`，len 2 995 945，BOM 保留，CRLF 48 563、裸 LF 0

## 一、开工靶池（实测 landed `f3f2e001`）

`stats`：375 ok / 27 partial / 0 failed，5657/5746。承接 Round 43 移交的线 D（前导/尾部整块未发射族）。

线 D 交付的两文件臂 `p12` 声称 `quote_handler.pyc 50→51/57`、`trade_live_broker.pyc 104→105/119`、
29 文件影响面 `SAME=23 IMPROVED=2 REGRESSION=0 MOVED=4`。本编排方在**私有臂 + 私有 ROOT** 下独立复测，
两条官方增益均复现，且 `get_index` 从 `orig=76 decomp=48` 变为逐指令 CLEAN。

## 二、根因（一条控制流事实，两个层面）

`quote_handler.pyc :: <module>.get_index` 形态：`l = len(index)` → 三条守卫 `if …: return` → 旋转 `while end - start > 1`。

1. **归属层（R44-A，`region_analyzer`）**：把候选前驱 `p` 并入 `LoopRegion.blocks` 前，未验证 `p` 是否真为本
   循环条件的操作数。CPython 条件 lowering 的结构事实是：`and`/`or` 复合条件的操作数链**只经 fall-through 边
   延续**，短路一侧永远是条件跳转目标。故若 `p` 的 fall-through 后继既不是链头 `_cb`、也不是 `header`、也不在
   循环体/已吸收链块内，`p` 就是**外层守卫**（`if c: return X` 后接 `while`）的条件块，而非循环条件操作数。
   误并后，外层 `IfRegion` 在生成阶段「块数多者胜」的包含判定中被丢弃，守卫链与循环前置语句一起无人发射
   （`get_index 76→48`）。判据只读 pred/succ 关系、fall-through 归属与块角色；只删不增。
2. **发射层（R44-B，`region_ast_generator`）**：回边块的终止指令是后向条件跳转（旋转 while 在回边处复制的
   那一次条件重算）。若块内除终止指令外不含任何「语句级」opcode 类（无 `STORE_*`、无 `POP_TOP`、无
   `CALL`/`DELETE_*`/`RAISE`/`IMPORT`/`YIELD`），则该块无可发射语句，整体就是条件表达式本身；此时不得按
   `_loop_find_cond_start_idx` 的切点从块首切出「前置语句」，否则条件左操作数（`end - start`）会作为裸表达式
   语句泄漏到循环体末尾（`get_index` 多 4 条，76→80）。只读 opcode 类。

## 三、隔离复测：两条合取缺任一条都测不到增益

| 臂 | 编辑 | 结果 |
| --- | --- | --- |
| `r44p1`（仅 R44-A） | region_analyzer | `quote_handler 50/57`、`scheduler 42/45` —— 与落地态逐位相同，零增益 |
| `r44p2`（仅 R44-B） | region_ast_generator | 29 文件面 `SAME=29 IMPROVED=0 REGRESSION=0`；唯 `get_index` 在官方 mism 上仍是缺陷，但产物从 `76→48` 变为 `76→44`（官方计数不变而实际更差） |
| `r44p12`（A∧B） | 两文件 | `quote_handler 51/57`、`trade_live_broker 105/119` |

⇒ 归属层给出的区域树需要发射层才能被正确写出，发射层的分支只在归属层产出的树上命中；两条同层判据互为零增益，
必须同轮落地。机制上这与 [[project-merge-completion-cascade]] 的「单点加合取项不单调」是同一枚硬币的两面。

## 四、门禁序列（严格串行）

- **G0 合成见证**（`D:/Temp/r43gate/g0pyc`，四支）：见证 `r43d_01_guardchain_then_while` 落地态 `1/2` → 候选 `2/2`；
  真反例 `r43d_02_compound_cond_control` 两臂产物 sha **逐字节相同**（判据不命中）；
  线 D 标注为反例的 `nc_controls` `6/7→7/7`、`nc_controls2` `6/7→7/7` 实为**额外见证**（命中并转好），非反例。
- **G1 deficit 池**：见 `g1x` 复测（本轮靶文件不在 G1 17 支内，改用线 D 两文件 + `flyAccount` 三支）。
- **G2′ 电池**：`test_repros` 143 支 `SAME=143 IMPROVED=0 REGRESSION=0`。
- **G3 锚点**：109 支 `same=108 lost=0`（`strategy.pyc` 在落地基线 jsonl 中缺行，非候选缺陷）。
- **G4 全 402 A/B（唯一发货判据）**：`SAME=400 IMPROVED=2 REGRESSION=0`，`Σmatched +2`。
- **G4′ 变更产物 strict 尺**：sha 变化面 **仅 6 支**（`execution_context`、`history_api`、`quote_handler`、
  `klinedata`、`plugin_system_trade/function`、`trade_live_broker`）；逐 code object 缺陷集合比对
  `affected=6 fixed=1 broken=0 changed=2`。strict 缺陷总数 48 → 47。

### 两条官方增益的成色不同（必读）

- `fly/data/quote_handler.pyc 50→51/57`：翻转函数 `get_index` 有 G4′ 的 `FIXED` 行佐证
  （`seq_len orig=76 decomp=48` → CLEAN）。**真实增益。**
- `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc 104→105/119`：翻转函数是
  `TradeLiveBroker.get_ipo_stocks`，G4′ **无对应 FIXED 行**，其 strict 判定由
  `seq_len 453→451`（少 2 条）变 `target_diff #189 POP_JUMP_IF_TRUE`（条数对、接错终点）——
  即官方尺因「只比跳转操作码」而把它算作 matched。**这是一枚假 ok，不是语义修复**，
  与 Round 42 否证 R42-A 的判据同源。本轮官方数字含此 1 支（`5659` 中 `+1` 为假 ok 所得），
  记入移交台账：`get_ipo_stocks` 与 `ipo_stocks_order`（`−1`→`+1`）必须在后续轮次里由 strict 尺转 CLEAN。

判定：本轮不满足「官方增益必须有 strict FIXED 佐证」的强判据（该强判据在 Round 42 用于**唯一**增益即为假 ok 的情形），
但满足门禁定义（G4 `REGRESSION=0` ∧ G4′ `broken=0`），且含一支完全验证过的真实修复。
线 D 代理建议「只发 P2」经独立复测为空增益（`SAME=29 IMPROVED=0`）且使 `get_index` 产物由 48 退到 44，不可取；
「只发 P1」则只有假 ok。故发货并显式披露成色差异。

- **G5 / G6 / G7**：见下节（落地后复验）。

## 五、发货决定

G4 `IMPROVED=2 REGRESSION=0` 且 G4′ `broken=0` ⇒ 发货。落地方式：把 `mirr_r44p12` 的两文件按字节复制回工作树，
落地后 sha 与镜像一致（已断言）。

## 六、落地后复验（G5 / G6 / G7）

- G5 `single`：`quote_handler.pyc`、`trade_live_broker.pyc` 各自重出产物后仍为 partial，残余缺陷函数与 G4 行一致
  （`get_index` 与 `get_open_orders` 均已从 mism 列表消失）。
- G6 `batch --index pyc_index.json --all --round 44`：`verified_pyc 402/402`，无 failed。
- G7 `stats`（本轮唯一发布数字，逐字）：

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5659
  cumulative_match_rate: 98.49%
```

## 七、Round 45 移交

1. **等长块换位（新确证形状，未收口）**：`fly/logger.pyc :: write_logging_thread` 官方 `113/113 j=1`，
   原始序列 `127 vs 128` —— 产品把 `if msgs: …info(msgs)` 块整体外置到函数尾并在原位留一条
   `JUMP_FORWARD`。同一族还有 `_process_task_queue 378/378`。这是**布局/次序**问题，不改条数只改排布，
   与 R44 两判据正交。
2. **反转 if + 丢失出口跳（新确证形状）**：`fly/simtradding/flyAccount.pyc :: init_connection` 官方 `42/41 j=0`，
   原始 `45 vs 44`：落点态发射 `POP_JUMP_FORWARD_IF_TRUE`（取反）而原始是 `IF_FALSE`，且原始
   `#38 JUMP_FORWARD #40`（假臂 → 循环外 return）在产品中被折叠为直接落到回边 —— 语义上把 break 降级成 continue。
3. **线 C 的 `c3`（守卫臂 merge 认领）不可发货**：`order_api 30→32/34`、`trade_live_broker 104→106/119` 但全语料
   `SAME=283 IMPROVED=3 REGRESSION=8`、Σ5523→5504、strict `fixed=10 broke=24`。其移交线索是**生成器洞**：
   兄弟块若起始于前一守卫区域的 merge 块，`region_ast_generator` 只发射第一个三元表达式
   （`get_open_orders` 在 c3 下丢 41 条尾块）。该线索在未附带 c3 的情况下也可能独立命中，优先按纯发射侧形状排查。
4. **线 A / 线 B 代理均耗尽 150 轮未交结论**。线 B 留下的 `r43b` 混合极性 or 链判据经本轮复测为
   **官方中性**（其 5 文件池 `flyAccount 21/23`、`logger 28/30` 与落地态完全相同），只修 strict 纯 target_diff；
   在当前目标（按 `stats` 计数）下优先级最低。
5. 台账更新：`quote_handler.pyc` 残余 6 函数（原 7）、`trade_live_broker.pyc` 残余 14 函数（原 15）；
   其中 `trade_live_broker` 的 `get_ipo_stocks`、`ipo_stocks_order` 本轮换了缺陷种类（前者 `seq_len`→`target_diff`，
   后者 `−1`→`+1`），仍属已失败函数，不新增损失。

