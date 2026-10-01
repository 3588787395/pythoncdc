# Round 1 修复工程师一报告（B1b 语句上下文混合 and/or 链 + B5 分离）

- 修复对象：B1b 核心 10 个 MISMATCH（r1_01/03/04/07/08/09/15/17/18/22）全转 MATCH；
  B5（CJB else-entry-only skip 第三丢弃入口候选）分离定位；B6 四上下文（r1_10/11/14/21）
  归修复工程师二，本批只记录状态。
- 唯一判据：`python scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元）。
- 硬约束自检：无函数名/文件名白名单、无 start_offset 数值阈值（偏移仅作块身份恒等比较）、
  无跨层读取（entry in other.blocks 类）、无新增 self 跨方法状态、被丢弃操作数全部接回；
  [R76-A1/A2] 守卫 wrap、[R75 fix1] 嫁接、B2 守卫族基线行为未回退
  （core/cfg/region_ast_generator.py 本批零改动，git diff 可证）。
- 未执行 git commit（主代理负责）。

---

## 0. 工作树状态如实声明（交接要点）

接手时工作树已含一段**同任务前序会话的未提交修复**（region_analyzer.py，`[B1b fix]`/
`[B1b fix-r2]` 标记）+ 临时调试钩子（`B1B_MERGE_DEBUG` env 门控文件写入、`import os as
_os_dbg` 函数内导入）+ 未跟踪调试产物（tmp_debug_b1b.py、.tmp_fix1_pre/、.tmp_fix1_probe/、
_b1b_merge_trace.log），无 FIX.md。本批在其基础上：清除全部调试钩子与调试产物、补齐触及
方法 docstring 三要素、以多臂开关 + 34 真身语料 A/B 实证审计每一臂、**以改进判据重写一臂并否决一
个引入语料回归的替代实现**（见 §3 多臂开关验证表与 C 臂权衡记录）、最终态全量复测。
FIX_B6.md 未存在（未读、未写）。

## 1. 根因定位（结构性）

### 1.1 链装配流程与丢失点

`if a and b or c:`（r1_01，块布局 block@0=LOAD a+PJIF→14 / block@10=LOAD b+PJIT→18 /
block@14=LOAD c+PJIF→28 / block@18=体 / block@28=汇合）在 3.11 的降级中，and→or 边界的
**or 尾操作数块（block@14）以「链尾成员 fall-through 后继」存在，而不是任何成员的跳转目标**。
链装配路径：

1. `_identify_boolop_regions`（region_analyzer.py:23480）→ `_detect_boolop_chain_start` →
   `_detect_boolop_conditional_chain`（:25235，模式 B 正向条件跳转链 walk）；
2. 混合链统一 `_try_unify_mixed_boolop_chain`（:27066）负责沿链尾 fall-through 续接
   失败路径上的未认领条件块；
3. 修复前该函数只做一次 `_detect_boolop_conditional_chain(ft_succ)` 多成员识别：
   or 尾裸操作数（单块、其 fall-through 恰为链真出口）因 Round 33「or 链成员不得作链首」
   守卫在该检测中返回 None，**续接失败即整体丢弃**——op_chain 停在 [and, and]，or 尾块
   脱离链、被 IfRegion 体/merge 剪枝吞并，条件重建退化 `a and b` + merge UNARY_NOT
   极性反转 → `if not (a and b):`，`LOAD_FAST c` + 条件跳转整体消失（与归档
   neg75_jqcond2、REVIEW 首分歧指令 f+5 逐位吻合）。

根因一句话：**`_try_unify_mixed_boolop_chain` 在「链尾成员（or 组）以正向 IF_TRUE 跳转
收尾、其后继是失败路径上未认领的单成员 or 尾」这一 CPython 标准降级形态上缺一条续接
判据，or 尾操作数块因此脱离 op_chain，后续消费端（_build_boolop_expression_inner 的
or_groups 分组、_if_extract_condition_from_instructions 的极性判定）按残缺链工作。**

### 1.2 触发条件（与 REVIEW 收敛一致）

and 组先行 + or 裸尾操作数。or 先行（r1_02/05/20）、双完整组（r1_06/16）、取反包裹
（r1_19）、纯表达式上下文（r1_13）不触发；嵌套（r1_04/07）、elif/try/for/with 臂内
（r1_08/17）、continue/break 守卫交叠（r1_09）、or 尾 return 臂（r1_18）、多语句体
（r1_22）均为同一根因的上下文变体。

## 2. 修复面（全部在 core/cfg/region_analyzer.py，共 6 处实质改动 + 触及方法 docstring 同步）

> region_ast_generator.py（共享家族 `_build_boolop_expression*`/`_graft_pending_operand`/
> `_cjb_*`/`_leading_*`/generate() wrap 段）**零改动**；B1b 的结构性根因在分析器链装配层，
> 修复亦在该层闭环，未动对方修复面（loop 条件装配 walk 的链首=header/condition_block
> 路径逐字节保持原 break）。

| # | 锚点（当前树行号） | 内容 | 条款 |
|---|---|---|---|
| A | `_try_unify_mixed_boolop_chain` :27153-27167 | **核心修复**：单成员 or 尾续接。判据 (1) 链尾成员链 op=='or' 且以正向 IF_TRUE 族跳转收尾（and→or 边界，跳转目标=链成功出口）；(2) 候选块以正向 IF_FALSE 族跳转收尾且假目标不指向真出口/链内任何块；(3) 候选块 fall-through 恰为链真出口（与 Round 33 据以拒绝其作链首的签名同源，此处反向用作「并回所属链」认领判据）。命中即按多成员 run 同款 op 推导（'FALSE'→'and'）追加进链，while 循环续接至无未认领条件块。完整链交 `_create_boolop_region_from_chain` 统一归约，消费端 or_groups 分组重建 `BoolOp(or,[and组, or尾...])`、极性不再反转 | C2（单 BoolOpRegion 黑箱组合）+ C3（失败路径孤儿块显式认领，无跨层读取：候选块 `ft_succ in self.block_to_region` 同层查表） |
| B | `_detect_boolop_conditional_chain` :26265-26276 | 主 walk 的 LoopRegion body_blocks 认领豁免：候选块被外层循环认领时，仅当 (a) 链首非该循环 header/condition_block（本 walk 是循环体内层 if 条件装配，[C1] 同层身份判定）且 (b) (current,candidate) 通过 `_b1b_loop_body_run_continuation` 三类降级续接判据，才放行；否则维持原 break。循环自身条件装配路径逐字节不变 | C1（同层身份）+ C3（显式守卫认领被循环认领的纯条件块） |
| B2 | `_try_unify_mixed_boolop_chain` :27114-27127 | 同一豁免在统一路径的镜像（循环体内 `if b or c and a:` 的 and-run 续接） | 同 B |
| C | `_identify_conditional_regions` :17434-17481（docstring :16015-16025） | continue-sink 邻接 elif 排除判据要求 else_succ 是纯条件块（测试跳转前无 STORE_*/BINARY_OP/DELETE_*/CALL+POP_TOP，与 `_sb_has_body` 同谓词）——CPython 把 post-if 语句与下一 if 条件测试合块，误判 elif 会使 merge 退化为循环出口、post-if 语句被吸进 else 臂（r1_09 的 B1b×B2 交叠面） | C1（只读本块指令 opcode 序列） |
| D | `_detect_boolop_conditional_chain` :25812-25845 | IfExp 真值块守卫收窄：fall-through 为纯控制 JUMP_FORWARD 块（除 POP_TOP/噪声无指令）时不再据此断链——(a) 含 POP_TOP（循环内 break 降级，r1_09）；(b) 裸 JF 且目标块不以 RETURN_* 收尾（空 then 臂跳 merge，trade_live_broker.on_pre_before_trading_start）。裸 JF 目标为 return 块（值上下文链尾签名，strategy.is_future_tradetime_now）与含其他指令块维持原 break | C1（块内 opcode 集 + 目标块末指令，同层结构事实） |
| E | `_detect_boolop_conditional_chain` :25997-26021 | chained compare 内部块不可吸收守卫：候选块∈某 chained compare IfRegion 的 `chained_compare_blocks` 且非其 entry 时断链（原则 2 每块唯一归属；上方 hop 机制以「内部块不进 op_chain」为前提）。**当前语料零触发（防御性不变量守卫）**：skip_claimed_check=True 有意绕过 claimed 守卫，此处为该绕行补 C3 显式排除 | C1（同层区域表成员关系）+ C3（显式排除被前置区域认领的块） |

新方法 `_b1b_loop_body_run_continuation`（:26921）：B/B2 共用的 (current,candidate) 降级
续接判定——(1) and→or 边界（current FALSE 族、candidate TRUE 族、candidate 落空边= current
假出口且该头仍为条件块）；(2) or-run 续接（current TRUE 族、candidate FALSE 族，沿
fall-through 走 ≤8 步 F-run，run 成员假边落同一假出口 Z≠Y、run 末 fall-through=Y）；
(3) and-run 续接（双 FALSE 族、假边共享出口；混合链 has_or_member=True 时豁免「共享出口
须为条件块」——末 or 组 and-run 假边共享链 merge）。current/candidate 同 TRUE 族拒绝。
判据全为块末 opcode 族与后继块身份。

**触及方法 docstring 三要素**：`_detect_boolop_conditional_chain`（:25235-25284，补 [B1b fix]/
[fix-r2]/IfExp 收窄/cc 守卫四段）、`_b1b_loop_body_run_continuation`（识别条件/归约方式/
AST 映射 + C1/C2/C3 全声明）、`_try_unify_mixed_boolop_chain`（同）、
`_identify_conditional_regions`（Step 5 补 [B1b fix] 段）；`_build_basic_if_region` 仅移除
调试钩子、无行为改动。

## 3. 单变量自证（多臂拆分逐个开关验证）

方法：`/tmp/b5probe/patch_arms.py` 逐臂禁用（其余臂保持），跑 10 目标 + strategy.pyc +
trade_live_broker.pyc。终版树（v4=A+B+B2+C+D收窄+E）读数：

| 禁用臂 | 10 目标 | strategy | trade_live_broker | 结论 |
|---|---|---|---|---|
| A（无单成员 or 尾续接） | **10/10 全部 1/2** | 26/27 | 118/128 | 核心，不可缺 |
| B（主 walk 无循环豁免） | r1_09 1/2，余 2/2 | 26/27 | **116**/128 | 必需（r1_09+2 单元） |
| B2（统一路径无豁免） | r1_09 1/2，余 2/2 | 26/27 | 118/128 | r1_09 必需（与 B 不同路径） |
| C（无 elif 纯条件块判据） | 10/10 全 2/2 | 26/27 | **120**/128 | 见下权衡 |
| D（IfExp 守卫还原 HEAD） | r1_09 1/2 | 26/27 | **117**/128 | 必需（r1_09+on_pre 单元） |
| E（无 cc 内部块守卫） | 10/10 全 2/2 | 26/27 | 118/128 | 零触发（防御性保留） |

**C 臂权衡记录**：C 的朴素替代「该分支无条件 merge=else_succ」实测 r1_09✓ 且 tlb=120，
但 34 真身 A/B 出现 **executor 9→8、quote 84→83 两处回归**（v5 语料 diff 留档
/tmp/b5probe/cab5.txt 摘要：executor −1、quote −1、tlb +5、trade_info_utils +1），违反零
回归纪律，弃用；C 臂（纯条件块判据）为 v4 终版：语料零回归。E 臂为正确性不变量
（skip_claimed_check 绕行 claimed 的 C3 补偿），当前零触发，如实登记。

## 4. 四项自测全量读数表（终版树，修复后）

### 4.1 自测 1：B1b 10 个 MISMATCH → MATCH（pycdc 重生成 *OK.py 后 single）

| 复现 | 判据读数 |
|---|---|
| r1_01_stmt_andor3 | success **2/2 100.00%** |
| r1_03_chain3 | success **2/2 100.00%** |
| r1_04_nested_if_mixed | success **2/2 100.00%** |
| r1_07_deep3_mixed | success **2/2 100.00%** |
| r1_08_elif_try_for_with | success **2/2 100.00%** |
| r1_09_continue_break_guard | success **2/2 100.00%** |
| r1_15_ifelse_mixed | success **2/2 100.00%** |
| r1_17_elif_mixed | success **2/2 100.00%** |
| r1_18_ortail_return | success **2/2 100.00%** |
| r1_22_multistmt_body | success **2/2 100.00%** |

r1_01 产物逐句对照：`if a and b or c: total += 4`（or 尾接回、极性正确，`if not (a and b)`
症状消失）；r1_03 三层混合链单条 if 重建（链拆裂消失）。

### 4.2 自测 2：负对照 + MATCH 组（--source 方式，未覆盖既有产物）

| 复现 | 读数 | | 复现 | 读数 |
|---|---|---|---|---|
| n1_01_simple_and | 2/2 100% | | r1_12_and_group_or | 2/2 100% |
| n1_02_simple_or | 2/2 100% | | r1_13_return_mixed | 2/2 100% |
| n1_03_uniform_and3 | 2/2 100% | | r1_16_two_groups | 2/2 100% |
| r1_02_stmt_orand | 2/2 100% | | r1_19_negated_mixed | 2/2 100% |
| r1_05_or_tail_compare | 2/2 100% | | r1_20_orlead_and | 2/2 100% |
| r1_06_paren_groups | 2/2 100% | | | |

**11/11 全绿，B1a 嫁接（r1_12）与全部形态边界无回退。**

### 4.3 自测 3：修复工程师二 4 复现（只记录，不修复；--source 方式）

| 复现 | 修复前（HEAD 基线） | 本批后 | 归属 |
|---|---|---|---|
| r1_10_while_mixed | MISMATCH | 1/2 50.00%（仍 MISMATCH） | B6（工程师二） |
| r1_11_ternary_mixed | MISMATCH | 1/2 50.00%（仍 MISMATCH） | B6（工程师二） |
| r1_14_assert_mixed | MISMATCH | 1/2 50.00%（仍 MISMATCH） | B6（工程师二） |
| r1_21_comprehension_mixed | MISMATCH | 1/3 33.33%（仍 MISMATCH） | B6（工程师二） |

### 4.4 自测 4：真身哨兵 + 回归组

| 目标 | 读数 | 基线对照 |
|---|---|---|
| IQCommon/strategy/jq_trans_module.pyc | **success 65/65 100.00%** | 命令达标（65/65）；failing_index 旧基线 63/65 |
| fly/data/quotation.pyc | 152/153 99.35% | 与基线持平（唯一失败 change_his_to_forward 同为基线失败），零新增 |
| round76 r76_01_guard_leak | 2/2 100% | [R76] 基线保持 |
| round76 r76_02_andchain_leading | 2/2 100% | [R76] 基线保持 |
| round76 r76_03_double_eval | 2/2 100% | [R76] 基线保持 |
| round75 neg75_jqcond（B1a） | 3/3 100% | 保持 |
| round75 **neg75_jqcond2（B1b 归档最小复现）** | **3/3 100%** | §6 验收判据达成 |
| round75 repro75_jqcond | 5/5 100% | 保持 |
| IQEngine/.../trade_live_broker.pyc | 118/128 | HEAD 115 → **+3**（零回归前提下的增益） |

**34 真身语料 A/B（HEAD 分析器 vs 本批，逐文件 units 对比）**：33/34 逐单元数完全一致；
唯一差异 trade_live_broker 115/128 → 118/128（+3，无任何文件回退）。

## 5. B5 分离结论（CJB else-entry-only skip 第三丢弃入口）

- **静态确证**：丢弃入口存在——region_ast_generator.py:48025-48033 判定（then 侧置
  `_cjb_pend_key`、else 侧只置 `_cjb_skip_inline_if`）+ :48038 嫁接守卫（`_cjb_pend_key
  is not None`）⇒ else-entry-only 触发时 `_cjb_cond_expr` 无嫁接（B1a 路径）无守卫登记
  （R76 路径）。
- **实证方法**：临时插桩（env 门控，验后即除）统计 `_cjb_skip_inline_if` 触发点。
  ①7 形态合成探针（for/while/try/with/内层 if-else 置于 else 臂、andor+else、
  then-侧对照）：8/8 单元全 100%，零 else-only 触发；②34 真身全量扫描：CJB skip 共
  触发 5 次，其中 **else-entry-only（pend=None）恰 1 次**：trade_live_broker.pyc
  `TradeLiveBroker.ipo_stocks_order` 块@2822（`... and node_type == '8'` 链中段成员，
  then=2864 非区域入口、else=2878=elif 链 IfRegion 入口）。
- **该次触发零信息丢失**：被丢弃候选（`node_type == '8'`）已由外层 IfRegion#1 的
  inline_boolop_chain 重建接回（反编译产物含完整链
  `submarket_type in (...) and node_type == '8' and stock_type == 'Y'` + continue）；
  ipo_stocks_order 单元失败为基线既有（REVIEW 前 failing_index 13 失败清单含该单元），
  与本批无关且非 B5 所致（首分歧另有根因）。
- **结论**：B5 丢弃入口真实存在、真身可达，但**未分离出独立信息丢失复现**——可达点均被
  链装配路径先行消费（操作数经 inline chain/BoolOpRegion 接回）。按任务纪律**不盲目单独
  修**，如实标注：B5 与 B1b 同源不同点（同一「条件操作数—区域边界」家族的第二丢弃口），
  登记为候选，交后续轮以「若 _cjb_pend_key is None 且 _cjb_pure_cond 非空，按同层后继
  结构判据显式认领或显式发射」为候选方案，须先构造出独立失败复现方可落地。

## 6. 遗留与交接

1. **B6 四上下文（r1_10/11/14/21）仍 MISMATCH**（§4.3 读数），归修复工程师二。提示：
   while/ternary/assert/comprehension 的消费端各自把残缺链物化成错误结构；A 臂（or 尾
   续接）只在 `_try_unify_mixed_boolop_chain`（If 语句上下文装配路径）生效，四上下文的
   装配入口不同（`_detect_while_condition_boolop_chain`/`_identify_ternary_regions`/
   AssertRegion boolop_chain/推导式筛选），需各自定位其「or 尾操作数块归属」丢失层，
   不得直接复用本批 if 路径判据（跳转极性与成功/失败出口语义在四上下文不同）。
2. **B5** 未修（§5），候选方案已给出，须独立复现先行。
3. **行为面变化声明**：jq_trans_module 65/65 保持，但 `trans_code` 单元源码形由
   `elif left_num == right_num: ... else:` 平化为 `if ... :` + 顺序 if（两形 recompile 均
   65/65，唯一判据通过；系 A 臂使链完整装配后 IfRegion 结构归并的自然结果）。
   trade_live_brokerOK.py 同步再生成（118/128）。
4. 观察登记 O1（守卫记录孤儿化）本批未触及守卫消费时序，r76_01/02/03 全绿防回归。
5. 临时产物已清理：tmp_debug_b1b.py、.tmp_fix1_pre/、.tmp_fix1_probe/、_b1b_merge_trace.log
   已删除；core/ 内无本批调试残留（region_ast_generator.py:21967 等处的 `R7_DEBUG_IFGEN`
   等 env 钩子为历史轮既有代码，非本批引入，未动）。
