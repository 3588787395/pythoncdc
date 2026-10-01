# Round 1 修复工程师二报告（B6：混合 and/or 链在四个非 if 上下文的消费族）

- 修复对象：B6 四上下文 r1_10（while）/ r1_11（ternary）/ r1_14（assert）/
  r1_21（comprehension）**4/4 全部转 MATCH**（另附带修复旋转 while 体内
  if-break 的既有丢失面，见 §2.5）。
- 基线：修复工程师一已落地的 B1b 核心（region_analyzer.py A/B/B2/C/D/E 五臂）
  为新基线，本批零回退（其修复面文件本批继续在同文件内改动，但未触碰其
  五臂判据逻辑；--source 全量复测见 §4）。
- 唯一判据：`python scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元）。
- 硬约束自检：无函数名/文件名白名单、无 start_offset 数值阈值（偏移仅作块
  身份恒等比较）、无跨层读取（归属校验只查同层 block_to_region 表）、无新增
  self 跨方法状态（新 helper `_b6_assert_absorb_and_run` 为纯函数式方法，输入
  链头/链块/已知集、输出前缀块）、被丢弃操作数全部接回；修复均为区域归约
  算法内的结构性判据，非逐形态补丁。
- 未执行 git commit（主代理负责）；FIX.md（修复工程师一）未改动。

---

## 0. 根因总览（四上下文各自一句话）

| 复现 | 根因一句话 |
|---|---|
| r1_10 while | 旋转 while 的 condition_block 落在混合链**中间**操作数（and→or 边界成员 B），既有装配全部单向：后向回溯收了 A 但 op 标签错标为「取反操作数」且 R07 all_same_target 对混合链必然拒绝；前向只收 [B or C] 残链——主扫描抢先以残链建 BoolOpRegion、Step 5 因「cond 已被 BoolOpRegion 含纳」整体跳过 ⇒ `if a: while b or c:` |
| r1_11 ternary | 混合链的 BoolOpRegion 装配**已完整**，但 `_build_ternary_condition_chain` 只认「全员共享同一假出口」的均匀链，链止于边界成员 B、or 尾 C 被当成 true_block → 值块守卫拒绝 → TernaryRegion 缺席，IfRegion 把残局物化成错序三元；即使建出 TernaryRegion，`_build_ternary_boolop_condition` 也把混合 op 压平成单 op（`a and b and c`） |
| r1_14 assert | assert 锚点落在链中段（or 成员 @10），`_reach_assertion_error_block` 对「链内条件块（2 后继）」直接失败 ⇒ 首操作数 A 不是合法锚点；既有 or-run 回溯（`assert not (or-chain)` 路径）只收 IF_TRUE 前驱，A（IF_FALSE）永远收不进 ⇒ `if a: assert b or c; return 1` |
| r1_21 comprehension | `_detect_comp_ternary`/`_extract_comp_ifs` 的「三元 vs 过滤器」甄别窗在跳转目标偏移处截断：混合链 and→or 边界成员的前向假边目标（or 尾成员块）之后才出现回跳 FOR_ITER 的条件跳转，被误判为三元条件 → 整链崩塌成 `b if a else 1`；即使段收集成功，组合器也只有单一 op（or/and 二选一），无法表达 and→or 组别边界 |

四上下文共享同一族缺陷（「and 组先行 + or 裸尾」的 op_chain 在各自装配入口
断链/错组），但断链层与消费端各不相同，按各自入口分别修复（判据同源：
块末 opcode 族 + 后继/前驱块身份，op 推导 'FALSE'→'and'/'TRUE'→'or' 与修复
工程师一 A 臂一致）。

## 1. 首个分歧指令（orig vs dec，dis 实测，修复前）

| 复现 | 首分歧 |
|---|---|
| r1_10 | f+5: `POP_JUMP_FORWARD_IF_FALSE to 18`（a 假边→c 测试）vs dec `to 50`（a 假边→整循环出口，`if a:` 包裹） |
| r1_11 | f+1: `POP_JUMP_FORWARD_IF_FALSE to 10` vs dec 错序三元 |
| r1_14 | f+1: `POP_JUMP_FORWARD_IF_FALSE to 10` vs dec `if a:` 包裹 |
| r1_21 | f+2: `MAKE_CELL c` 缺失（c 从产物消失）；listcomp 控制流整链崩塌 |

## 2. 修复面（3 个文件、7 处实质改动 + 触及方法 docstring 三要素）

### 2.1 while 条件装配 — core/cfg/region_analyzer.py
- **`_detect_while_condition_boolop_chain` :24459（[B6-while 混合链双向续接]）**
  后向回溯产链（≥2 且链首原始跳转为 IF_FALSE 族、链尾=condition_block 以
  IF_TRUE 族跳 header）时识别混合形态：①op 重标（链首按其自身跳转方向
  'FALSE'→'and'，废除「取反操作数」误标）；②or 尾前向续接——从
  condition_block 的 fall-through 起，凡不在 loop.blocks、以正向条件跳转
  收尾的块：IF_TRUE 族且真目标=链尾真目标者为中间 or 成员（沿
  fall-through 继续），IF_FALSE 族且 fall-through=header（完备性闭合）、
  假目标不指向链内/真出口者为末 or 尾成员（终止）；③边界闭合：链首假边
  目标必须恰为第一个 or 尾成员。混合链不经 all_same_target（结构性不满足
  而非嵌套信号），均匀链原判据逐位不变。
  [C1] 同层块末 opcode 族与后继块身份；[C2] 完整链交
  `_create_boolop_region_from_chain` 单 BoolOpRegion 黑箱组合；
  [C3] or 尾块归属由 Step 5 调用方所有权校验保证。
- **`_identify_boolop_regions` Step 5 :24017（[B6-while 所有权校验与残链超越
  替换]）** 重构守卫顺序：先装配链再判所有权——链块仅允许「未认领 / 本
  LoopRegion（condition_block 惯例）/ 待超越残链 BoolOpRegion」三类持有者；
  残链超越判据（同层结构事实）：主扫描残链的 entry 是完整链的**非首成员**
  且 op_chain 更短 ⇒ 撤销残链（块归还 block_to_region、注销 regions/
  children）后按完整链重建。docstring Step 5 段同步。
  **`_detect_while_condition_boolop_chain` :24194 新增 docstring 三要素。**

### 2.2 旋转 while 体内 if-break — core/cfg/region_ast_generator.py
- **`_loop_generate_while` :6536（[B6-while 循环体 if-break 修复过滤]）**
  原 889a0417 过滤把 boolop 复合条件 while 体内**所有**顶层 `If(body 含
  Break)` 语句整体丢弃（历史用途：遮蔽 else 侧物化破坏）。实测该丢弃使
  r1_10/ref_break2/ref_break3 的 break 消失（控制流改变）。修复按 else 侧
  内容三分：orelse 为「整条无语句 elif 链」（每个 elif body 仅 Pass、链尾
  orelse 空——回边重检链零语句的结构签名，`_b6_stmtless_elif_chain`）⇒
  剥离 orelse 保留 if-break；orelse 含真实语句 ⇒ 维持原丢弃逐位不变；
  orelse 空/None 的干净 if-break ⇒ 保留。修复前该丢失为**既有缺陷**
  （`while a and b:` + break 在基线即失败），不修则 r1_10 无法闭合。
  [C1] AST 结构签名；[C2] IfRegion 黑箱消费；[C3] 显式三分守卫。

### 2.3 assert 条件装配 — core/cfg/region_analyzer.py + region_ast_generator.py
- **`_b6_assert_absorb_and_run` :15386（新方法）** 从链头沿未认领前驱吸收
  and-run 前缀：前驱 P 以正向条件跳转收尾、fall-through=链头、P 假边目标
  ∈ 已知链块集（and→or 边界签名）；吸收后整链 op 逐块按跳转方向重导
  （'TRUE'/'NOT_NONE'→'or'，否则 'and'），返回 (run 首, 全链块, len(链)+1
  个 op)。docstring 三要素 + C1/C2/C3 全声明。
- **`_detect_assert_boolop_chain` :15358（[B6-assert 后向 and-run 前链吸收]）**
  前向链非空与 or-run 回溯（`assert not (or-chain)` 既有路径）两处接入：
  吸收后 condition_block 按「入口引用语义」重映射为 run 首（复用既有
  new_condition_block 通道）。docstring [B6-assert] 段同步。
- **`_build_assert_boolop_condition` :3969（region_ast_generator.py，
  [B6-assert op 契约扩展]）** 兼容契约：len(chain_ops)==len(all_blocks) 时
  ops 逐块对齐（新契约，混合链需要 cond op ≠ chain0 op）；否则维持旧契约
  （chain_ops[0] 复用标注，纯链逐位等价）。or_groups 分组重建
  `A and B or C`。

### 2.4 ternary 条件消费 — region_analyzer.py + region_ast_generator.py
- **`_detect_ternary_pattern` :21834（[B6-ternary BoolOp 驱动链升级]）**
  链 walk 止步于既有 BoolOpRegion（entry==block 身份恒等、op_chain≥2）的
  非末成员时：若末成员以正向条件跳转收尾、跳转目标=该区域 merge_block
  （or 尾假出口=三元假值块的接口闭合）、其两路后继均为直线值块
  （不含任何条件跳转）⇒ chain_blocks 升级为该 BoolOpRegion 的 op_chain
  链块（op 信息由既有 boolop_op_chain 升级通道携带），交下方既有
  len(chain)>1 路径与 skip_ternary 守卫建 TernaryRegion。
  [C2] 经 entry/merge 接口黑箱消费 BoolOpRegion，不重走链内部。
- **`_build_ternary_boolop_condition` :35368/:35374（[B6-ternary 混合 op
  分组]）** 逐操作数记录 op：全部一致时维持原左折叠形态逐位不变；存在
  组别边界时按 or_groups 分组（and 绑定比 or 紧，与
  `_build_boolop_expression_inner` 同一算法）重建混合 BoolOp。
  docstring 原文「不处理混合and/or」同步改为 or_groups 声明。

### 2.5 comprehension 过滤链 — core/cfg/comprehension_generator.py
- **`_detect_comp_ternary` :1875 / `_extract_comp_ifs` :1423（[B6-comp 混合
  过滤器甄别扩展]）** R10 甄别窗（回跳条件跳转只搜 [跳转, 目标) 区间）
  扩展：[目标偏移, append) 内存在回跳 FOR_ITER 的条件跳转、且其前一条
  指令为非跳转（回跳与操作数求值同块——块为极大直线序列，过滤器成员
  专属签名；三元假值块为直线求值、三元作过滤器的回跳出口块为裸跳转块，
  均不命中）⇒ 判过滤器：`_detect_comp_ternary` 返回 None 交回逐段提取，
  `_extract_comp_ifs` 收集该段继续。不命中维持 R10/R67 原判据逐位不变。
- **`_extract_comp_ifs` :1570/:1597（[B6-comp 混合 op 标注/分组]）** 逐段
  按跳转方向标注组别 op（前向 IF_TRUE=or 成员；回向 IF_TRUE=取反 and
  成员；其余=and 成员）；全部段同 op 时走既有单 op 路径（含多行
  raw-text 逻辑）逐位不变；存在组别边界时 or_groups 分组重建混合
  BoolOp。docstring（`_detect_comp_ternary`）[B6-comp] 段同步。

## 3. 单变量自证（逐改动隔离验证）

| # | 改动 | 验证 |
|---|---|---|
| 1 | while 混合链双向续接（2.1 第一条） | 单独落地后 r1_10 条件正确（`while a and b or c:` 接回），但 break 仍缺（既有缺陷，见 3）→ 配合 2.5 后 r1_10 2/2 |
| 2 | Step 5 所有权校验/残链超越（2.1 第二条） | 与 1 同批必需：无超越则主扫描残链 [b or c] 抢先、Step 5 被旧守卫跳过；r1_01 组 10 目标 + n1 组复测零回退 |
| 3 | if-break 修复过滤（2.2） | 单独落地后 ref_break2（`while a and b:` + break，基线即失败）转好且 r1_10 2/2；ref_break1（非 boolop 条件，不走该过滤）逐位不变 |
| 4 | assert and-run 吸收 + op 契约扩展（2.3） | r1_14 2/2；ref_assert1/2/3（纯 and / 纯 or / 带消息）产物逐字节不变（新契约分支不触发） |
| 5 | ternary BoolOp 驱动链升级 + 混合 op 分组（2.4） | r1_11 2/2；ref_tern1/2（均匀链）产物逐字节不变（升级条件要求 walk 止步于非末成员，均匀链不触发） |
| 6 | comp 甄别扩展 + op 标注/分组（2.5） | r1_21 3/3；ref_comp1/2/3/4/5 产物逐字节不变（甄别扩展仅命中「目标偏移之后 + 融合回跳」签名） |

## 4. 四项自测全量读数表（终版树）

### 4.1 自测 1：B6 四个 MISMATCH → MATCH（pycdc 重生成 *OK.py 后 single）

| 复现 | 判据读数 |
|---|---|
| r1_10_while_mixed | success **2/2 100.00%**（`while a and b or c:` 完整 + `if n > 9: break` 回归） |
| r1_11_ternary_mixed | success **2/2 100.00%**（`x = 1 if a and b or c else 2`） |
| r1_14_assert_mixed | success **2/2 100.00%**（`assert a and b or c`，`if a:` 包裹消失） |
| r1_21_comprehension_mixed | success **3/3 100.00%**（`[1 for _ in range(3) if a and b or c]`，f 单元 + listcomp 单元 + MAKE_CELL 全对齐） |

### 4.2 自测 2：修复一成果不回退（--source 法，临时产物写系统临时目录）

round1 全组 25/25 全绿（--source 法逐个重反编译）：

| 组 | 读数 |
|---|---|
| B1b 10 目标（r1_01/03/04/07/08/09/15/17/18/22） | **10/10 全 2/2 100%** |
| MATCH 组（r1_02/05/06/12/13/16/19/20） | **8/8 全 2/2 100%** |
| 负对照（n1_01/02/03） | **3/3 全 2/2 100%** |

### 4.3 自测 3：真身哨兵

| 目标 | 本批读数 | 基线对照 |
|---|---|---|
| IQCommon/strategy/jq_trans_module.pyc | **65/65 100.00%** | 达标（65/65） |
| fly/data/quotation.pyc | **152/153 99.35%** | 与基线持平（唯一失败 change_his_to_forward 同为基线既有），零新增 |
| IQEngine/.../trade_live_broker.pyc | **118/128 92.19%** | 不低于基线 118/128，持平 |
| round76 r76_01_guard_leak / r76_02_andchain_leading / r76_03_double_eval | **各 2/2 100%** | [R76] 基线保持 |
| round75 neg75_jqcond / **neg75_jqcond2（B1b 归档最小复现）** / repro75_jqcond | **3/3、3/3、5/5 全 100%** | 保持 |

### 4.4 自测 4：failing_index 抽验（9 个 ≥ 6 个要求，含指定 2 个）

| 文件 | 基线（failing_index.json） | 本批（--source 法） | 回退 |
|---|---|---|---|
| fly/data/quote.pyc | 81/92 | **84/92** | **+3（增益）** |
| IQCommon/util/trade_info_utils.pyc | 36/41 | 36/41 | 0 |
| IQCommon/util/email_utils.pyc | 3/4 | 3/4 | 0 |
| IQEngine/core/executor.pyc | 9/10 | 9/10 | 0 |
| fly/common/future_contract_info.pyc | 27/29 | 27/29 | 0 |
| IQEngine/data/trading_dates_mixin.pyc | 13/14 | 13/14 | 0 |
| IQCommon/api/klinedata.pyc | 61/64 | 61/64 | 0 |
| IQEngine/core/bar.pyc | 84/85 | 84/85 | 0 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 26/27 | 26/27 | 0 |

quote +3 为 B6 修复（comprehension 过滤链 / while 条件装配）在真身语料的
自然增益，无任何文件回退。

## 5. 遗留与交接

1. **ref_tern3/ref_tern4（本批新增探针，非任务矩阵）**：三元上下文的
   or→and 方向混合链（`1 if a or b and c else 2`）与 and 内嵌 or
   （`1 if a and (b or c) else 2`）仍 MISMATCH（基线即 1/2，本批零回退）。
   根因与 r1_11 同族不同向：or→and 边界的前向 walk 断链（BoolOpRegion
   本身残缺），`_try_build_and_inner_or_pattern` 的 and 内嵌 or 判据在
   三元上下文（值块=假值块出口）不成立。交后续轮：or→and 方向的续接
   判据（候选块假目标=or 尾共享出口的 and-run 续接）+ 三元上下文的
   and 内嵌 or 重建。
2. **ref_comp6（本批新增探针）**：`a and (b or c)` 过滤器仍输出
   `a or b or c`（基线即失败，零回退）。or_groups 无法表达「and 在外、
   or 在内」，需 comprehension 侧补 and-inner-or 检测（镜像
   `_try_build_and_inner_or_pattern`，值出口=循环体入口）。
3. **while 家族残留探针**：`while a and (b or c)` / `while a and b or c or d`
   / `while (a and b) or (c and d)` / `while a or b or c and d` 在基线即整
   循环丢失（探针实测 1/2），本批未触及（r1_10 形态已闭合）；其完备性
   判据可复用本批 [B6-while] 的边界闭合 + or 尾续接框架，交后续轮。
4. quote +3 增益涉及的单元未逐一登记（quote 真身 92 单元级验证全过），
   无回退面。
5. 本批零调试残留：探针目录 `.tmp_b6probe/` 已删除；core/ 内无 env 门控
   新增（历史 R23N21_DEBUG 等钩子未动）。
