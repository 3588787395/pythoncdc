# Round 6.3 复核（评审工程师 · 对抗复核批次）

- 复核人：评审工程师（Round 6.3，独立复核，零容忍）
- 日期：2026-10-03
- 复核对象：四批修复 commit `fbfc2e7b`（B29/B32 + w_with_if 两级）/ `1c059d1b`（B29-af_try break + B33 UNPACK_EX）/ `4cd2a9f6`（B35 + B30）/ `30468033`（B34c + B34b）
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；全部 `*OK.py` 仅经 `pycdc.py -o` 再生成，零手改；未修改 core/、parsers/、scripts/、pycdc.py 及 REVIEW.md/FIX.md/spec.md/tasks.md；全部命令 ≤300 s。
- 复核手段：① 四 commit 全量 diff 逐 hunk 合规审查（A1–A10）；② 读数独立复跑（round6 batch + 六哨兵 + round5 抽验 + 追加 option_account 哨兵）；③ 7 个新变体探针攻击（修复前树 worktree 归因对照）。

---

## 终判：**打回**

打回不是因为读数虚报（读数复跑 **21/21 面全部与声明持平、零虚报**），而是因为**存在不可通容的合规红线违规**与**变体攻击新登记破口**，具体打回项见 §5：

1. **[A10 红线] `fbfc2e7b` 第一 hunk 剥除了 `core/cfg/region_ast_generator.py` 的 UTF-8 BOM（G0 守卫），此后至今未恢复**——round6 评审时点（4135e6db）实测 `efbbbf` 在位（round6 REVIEW §4-8 亦判「在位 ✓」），修复批次一将其剥离为裸 `"""`，`git show` 逐 commit 验证四批修复及收官快照均无 BOM。
2. **[A8] `4cd2a9f6` 静默移除 `_generate_with` 主块循环的 `BlockRole.LOOP_BACK_EDGE` 跳过分支**（R8 validate_data / R66 option_account 两代判据），FIX.md 零声明。实测 option_account 35/35 无回归，但「后批静默更改既有判据」本身即违规。
3. **[A9] `4cd2a9f6` 删除 `import sys as _sys` 却保留同闸门内引用 `_sys.stderr` 的调试 print**（region_ast_generator.py:733/:803，R23N21_DEBUG 门控）——插桩残留被触碰后呈破损态（env 置位即 NameError）。
4. **[A7] 4 个新方法缺 C1/C2/C3 条款声明**（三要素在位）：`_b31_continuation_owner`(:9278)、`_const_code_is_async_comprehension`(:9348)、`_b34c_is_exit_window`(:9881)、`_b34c_has_held_replace`(:9864)。
5. **[变体攻击] 新登记 B37–B41 五破口族（11 单元）**：round6 全清 115/115 成立，但「With/AsyncWith + async 五件套」在宿主结构/嵌套深度改变下仍有 5 个未覆盖形态族（全部经修复前树归因为**既有缺口**，非修复引入回归）。

---

## §1 逐 hunk 合规审查表（A1–A10）

判定口径：✅=通过；❌=打回项；⚠️=缺陷记录（不单独构成打回，与 §5 合并计）。

### Commit 1 `fbfc2e7b`（3 文件 21 hunk）

| # | 文件 | hunk（@@ 锚点） | 判定 | 机制说明 |
|---|---|---|---|---|
| 1 | region_ast_generator.py | `@@ -1,4` | **❌ A10** | 剥除 BOM：`-﻿"""` → `+"""`。评审时点 4135e6db 实测首 3 字节 `efbbbf`，本 hunk 后永久丢失（1c059d1b/4cd2a9f6/30468033/eedb08cc 及工作树均 `222222`）。G0 守卫违反，无任何声明。 |
| 2 | region_ast_generator.py | `@@ -145,7`（import） | ✅ | 引入 `is_async_poll_protocol_block` 共享事实源，无判据变化。 |
| 3 | region_ast_generator.py | `@@ -1738,6`（generate() 清理尾声预标记 B31 豁免） | ✅ | 判据 = `_collect_await_protocol_chain` 链形态 + `_b31_continuation_owner` 延续形态，纯操作码/块身份；A2 无偏移魔数；A4 无新 self 状态。 |
| 4 | region_ast_generator.py | `@@ -3273,6`（IfRegion 顶层协议消费入口） | ✅ A3 | `_consume_top_level_async_protocol_if`：IfRegion.blocks ∩ WithRegion.blocks 非空交集 + 协议特征码（PUSH_EXC_INFO/WITH_EXCEPT_START/RERAISE 等，用户代码不可达）。区域树同层事实，非跨层回溯修正；用户 if 含用户指令即拒绝（C3 双向）。 |
| 5 | region_ast_generator.py | `@@ -7914,6`（LOOP 体首挂起轮询块消费） | ✅ | 复用 `comprehension_generator.is_async_poll_protocol_block`（与 r5 B23 `_find_async_clause_heads` 同源 ASYNC_POLL_PROTOCOL_OPS，零复制判定）；SEND+回环自跳+region.is_async 三重结构事实。 |
| 6 | region_ast_generator.py | `@@ -8881,6`（+234 行：`_collect_await_protocol_chain`/`_b31_continuation_owner`/`_const_code_is_async_comprehension`/`_b31_await_chain_gate`） | ✅/⚠️ A7 | 判据全为操作码形态+SEND argval 目标块+身份去重（A1/A2 过）；BEFORE_* 领地拒捕（B29 边界清晰）。⚠️ `_b31_continuation_owner`(:9278)、`_const_code_is_async_comprehension`(:9348) 三要素在位但无 C1/C2/C3 条款。 |
| 7 | region_ast_generator.py | `@@ -29703,6`（`_consume_async_with_protocol_if`/`_consume_top_level_async_protocol_if`/`_consume_async_exit_chain_region`） | ✅ | 协议特征码集合（仅异常表协议可产生）+ RETURN 终结链自证；A3 合规（宿主定位在本层 regions 集合内）；六段注释在位。 |
| 8 | region_ast_generator.py | `@@ -29916,6`（`_walk_async_pending_return`/`_extract_async_enter_chain_target`） | ✅ | BFS 机器形态块白名单 = 操作码集合，无偏移；`_steps < 8` 为走查步数预算（非 start_offset 魔法阈值）。`_extract_async_enter_chain_target` 仍只认出口块首条 STORE_* 单名——**该单名假设即 §3 rv6_06（B41）async 宿主 withitem 目标丢失的锚点之一**（判据面窄于 r6_09 同步面，B33 批次未同步覆盖 async 入口链，记入新破口机制）。 |
| 9 | region_ast_generator.py | `@@ -30084,20`（with_blocks[0] 启发式移除 → 链提取） | ✅ | 移除旧单名启发式，换 `_extract_async_enter_chain_target` 结构判据；判据收窄方向（更严），行为变化已声明。 |
| 10 | region_ast_generator.py | `@@ -30176,9`（W11-A 祖先链判定） | ✅ | parent 链上溯替代「entry ∈ 候选 blocks」单判据，区域树事实；防无限递归。 |
| 11–12 | region_ast_generator.py | `@@ -30277,7` / `@@ -30376,7`（嵌套区域生成前两个协议消费接入点） | ✅ | 与 #4/#7 同判据源调用，无复制判定。 |
| 13 | region_ast_generator.py | `@@ -30435,6`（纯机器块 Expr(Await(Call(Constant None))) 伪影剔除） | ✅ | 判据 = 块操作码全集 ⊆ {POP_TOP, JUMP_*, 噪声} ∧ func=Constant None；「None 不可调用」语义自证，无名字/偏移。 |
| 14 | region_ast_generator.py | `@@ -30535,6`（async 体尾挂起值升级 + 退出链消费 + 纯机器 Return 剔除） | ✅ | `_walk_async_pending_return` 共享判据源；RETURN_CONST None 隐式形态禁升级（双向判据）。 |
| 15 | region_ast_generator.py | `@@ -31199,6`（装配后链消费 + 体尾升级） | ✅ A3 | 候选链头 = 本层块 ∪ 直接后继（链头可能为子区域块的边界事实），walk 命中才标记；exc 块标记限于 region.exc。 |
| 16 | region_ast_generator.py | `@@ -46017,7`（`_generate_block_statements_body` 伪影漏斗 + B32 内联 BFS 升级） | ✅ | 两漏斗均语句结构/操作码形态判据；B32 BFS 后于 `4cd2a9f6` 因子化为 `_pending_value_protocol_hit`（FIX.md B32 章声明，非静默）。 |
| 17 | region_ast_generator.py | `@@ -46107,6`（B31 gate 前置分流） | ✅ | gate 返回 `[]`（非 owner 禁发射）维持每块唯一归属。 |
| 18 | region_analyzer.py | `@@ -7548,6`（`_check_return_for_break` 前隐式 return None 形态排除） | ✅ | 判据 = RETURN_CONST None / LOAD_CONST None+RETURN_VALUE 编译器确定形态，结构事实。 |
| 19 | region_analyzer.py | `@@ -7602,13`（自循环豁免无条件化） | ✅ | 行为变化有注释链与机制论证（挂起轮询自循环与外层循环无关）；方向为放宽且由 round6 全量零回归背书。 |
| 20 | region_analyzer.py | `@@ -12016,6`（`_extend_with_body_end` RETURN_* 融合块放行） | ✅ | 融合块（协议+return 同块、无后继）vs 嵌套清理块（JUMP/fall-through 转移）终结指令互斥区分，结构事实。 |
| 21 | region_analyzer.py | `@@ -12308,7`（R84 收窄：裸 return 块保留 target） | ✅ | 判据 = 块内是否含 SWAP/PRECALL/CALL 协议指令，操作码形态。 |
| — | comprehension_generator.py | `@@ -5,43`（ASYNC_POLL_PROTOCOL_OPS + is_async_poll_protocol_block）+ `@@ -1212,8`（_tail_ops 派生） | ✅ | 单一事实源重构；新旧集合逐项相等（`OLD == ASYNC_POLL_PROTOCOL_OPS - {'SEND'}`），行为保持。 |

### Commit 2 `1c059d1b`（2 文件 2 hunk）

| # | 文件 | hunk | 判定 | 机制说明 |
|---|---|---|---|---|
| 1 | region_analyzer.py | `@@ -12951,12`（`_extract_with_items` UNPACK_EX 分支） | ✅ | UNPACK_EX argval 低 8 位 before/高 8 位 after 与 CPython 协议一致；Starred 位 = before+1。判据 = BEFORE_WITH 后操作码形态链。⚠️ 流程观察：round6 REVIEW §6 要求「B33 复用/共享 `_parse_target_store_sequence`」，本批为内联新写——后经 `30468033` 重写为递归 `_parse_bind_unpack`（更一般结构解析器），非单形补丁，判据合规，记为对交接建议的偏离（可举证反驳成立）。 |
| 2 | region_ast_generator.py | `@@ -27416,6`（`_generate_try` handler break 直跳判据） | ✅ | 判据 = 纯异常栈清理（POP_EXCEPT/POP_TOP/POP_BLOCK）+ 无条件 JUMP 终结 + 目标 ∈ LoopRegion 及全部后代块集之外 → Break；区域归约语义四出口互斥论证在注释内。A2/A3 合规。 |

### Commit 3 `4cd2a9f6`（17 hunk，region_ast_generator.py）

| # | hunk（@@ 锚点） | 判定 | 机制说明 |
|---|---|---|---|
| 1 | `@@ -259,6`（`_STMT_BARRIER_OPS` 类级事实源） | ✅ | 操作码集合常量；B35/B30 共用，零复制。 |
| 2 | `@@ -695,7` | **❌ A9** | 删除 `import sys as _sys`，但保留 `print(..., file=_sys.stderr)`（:733，R23N21_DEBUG 门控）→ 调试残留呈破损态（置位即 NameError）。既有插桩未清且被触碰破坏。 |
| 3 | `@@ -767,7` | **❌ A9** | 同上（:803）。 |
| 4 | `@@ -4411,6`（B35 混合 else 块拆分） | ✅ | GYFI 反向走查至 `_STMT_BARRIER_OPS` 屏障；前缀归本环 else、后缀归后继环；判据为操作码形态+块内偏移序（非 start_offset 阈值）。六段注释在位。 |
| 5 | `@@ -5112,6`（B36-f 两段认领） | ✅ 判据 / ⚠️ 精简 | 判据 = else 链穿透 + RETURN 块唯一非异常前驱 ∈ else 链 + `_detect_with_body_return` 命中 + 归属台账占用者为祖先 with 区域——全同层结构事实，A1/A2/A3 过；`_b36f_claimed` 先于两段初始化（FIX.md 声明的初版回归修正）。⚠️ **两段约 40 行走查代码逐字复制两份**（:5228-5296 与 :5296+），违反 FIX.md 自己的「唯一事实源，禁止复制判定」原则（完备精简扣分项）。 |
| 6 | `@@ -7243,6`（`_generate_loop` 体装配前 B34 认领接入） | ✅ | `_b34_unclaimed_loop_resume` 定位 + `_b34_loop_resume_pending_return` 改判，判据见 commit 内两方法（GET_ANEXT 头 + SEND 自循环 poll + resume ∉ region.blocks + 祖先台账放行），结构事实。 |
| 7 | `@@ -9052,6`（`_pending_value_protocol_hit` 因子化） | ✅ | B32 BFS 抽取为唯一事实源；SWAP 跨块已见即命中 + PUSH_EXC_INFO 不穿越；FIX.md B32 章声明，行为超集非静默。 |
| 8 | `@@ -9106,6`（B31 gate 前置 B34 领地守卫） | ✅ | `__aexit__` 消费链头形态（SWAP+CALL+GET_AWAITABLE+≥3 个 None 常量）拒捕，防跨层级发射；操作码形态判据。 |
| 9 | `@@ -9156,6`（+377 行：`_b33_await_owner_merged_stmts`/`_b36_cross_block_return_value`/`_b34_unclaimed_loop_resume`/`_b34_loop_resume_pending_return`） | ✅ | 全部判据为链成员操作码/后继边/归属台账；junction ∈ region.with_blocks 跨区域链禁捕（A3）；每块唯一归属全链标记；六段注释齐备。 |
| 10 | `@@ -26488,6`（`_b30_held_replace_pair_value`） | ✅ | 形态判据与 FIX.md B30 章逐条一致（B1 末两条 SWAP(2)+POP_TOP、vi==0 自查块首、B2 中段 ⊆ {LOAD_CONST,PRECALL,CALL,POP_TOP}+恰 3 None+CALL+尾 POP_TOP）；已知失败模式记录在注释（C3 守卫）。 |
| 11 | `@@ -26757,7`（find 侧复合门控块对分支） | ✅ | `len(seq)==2 ∧ 块对判据` 才放行，未命中维持原拒绝路径（零放宽风险）。 |
| 12 | `@@ -28009,6`（W11-A 发射侧块对整体归约） | ✅ | 唯一正常后继 + `_w11a_nc_offsets` 成员 + 判据命中 → Return + 双块标记 generated；B2 不独立发射。 |
| 13 | `@@ -30717,9`（移除 `BlockRole.LOOP_BACK_EDGE` 跳过） | **❌ A8** | **FIX.md 零声明的行为变更**：该跳过分支系 R8（validate_data）/R66（option_account，da260298）两代落地判据，本 hunk 在 with 主块循环中静默删除。追加哨兵复验 option_account = 35/35（R66 100% 基线持平），未实测出回归，但「后批静默更改既有判据」直接违反批次一致性纪律；且其动机未在任何注释/FIX.md 中论证。 |
| 14 | `@@ -31056,8`（`_generate_with` 体循环 B33 junction 接入点） | ✅ | gate 调用点置于 `_detect_with_body_return` 之前；判据源唯一。 |
| 15 | `@@ -31102,6`（B36-e 跨块值提取 + B33 二次发射剔除） | ✅ | B36-e：仅当 return_info 值为 Constant None 且 `_b36_cross_block_return_value` 命中才替换（FIX.md 声明「保留启用」）；B33 剔除：块首 UNPACK_* + Assign 目标元素名与 region.items 元组目标逐一同名（名字同一性来自同一 STORE 链，非用户名白名单）。 |
| 16 | `@@ -46825,10`（B32 漏斗注释 + 尾部 SWAP+POP_TOP 剥除） | ✅ | 剥尾 SWAP+POP_TOP 挂起保存对（协议指令非值消费点），升级仍由 `_pending_value_protocol_hit` 把关。 |
| 17 | `@@ -46841,29`（B32 内联 BFS 替换为 helper 调用） | ✅ | 判据面同 #7，负复制。 |

### Commit 4 `30468033`（6 hunk）

| # | 文件 | hunk | 判定 | 机制说明 |
|---|---|---|---|---|
| 1 | region_analyzer.py | `@@ -7757,6`（`_detect_with_body_return` 无 SWAP 无值窗口返回 None） | ✅ | FIX.md B34c §5 声明的配套改判；方向：值块侧整链归约，with 体空；有 SWAT 路径维持原状。 |
| 2 | region_analyzer.py | `@@ -12149,13`（`_collect_normal_exit_cleanup` 签名 + 可达性 BFS） | ✅ | 种子 = entry∪body∪exception_blocks 前向正常可达；三类不穿越（已归属块/其他 with 种子/外部 WITH_EXCEPT_START 处理器）。判据全为控制流边性质+区域归属（A1/A2/A3 过）；「已知失败模式」防重蹈段在注释。A4：复用既有 `self.block_to_region`，无新 self 状态。 |
| 3 | region_analyzer.py | `@@ -12260,6`（B36-a 结论注释追加 + C3 可达性过滤 + bare-None 细化） | ✅/⚠️ | 细化判据双向（条件假边直达收编 / 无条件边拒收）与 FIX.md 声明一致；判据为前驱终结操作码性质 + 去噪后 bare-None 形态。⚠️ 记录：代码的「去噪」集（RESUME/NOP/CACHE/PUSH_NULL/POP_TOP/JUMP_FORWARD/JUMP_ABSOLUTE/POP_EXCEPT/COPY/RERAISE/SWAP）宽于 FIX.md 字面「去噪后恰为 [LOAD_CONST None, RETURN_VALUE]」的朴素读法，FIX.md 未列噪声明细——双向形态验证（check_trade_name 80/80 + r6_10 6/6 + 本复核 rv6_03 4/4）未发现越界，记为声明颗粒度缺陷。 |
| 4 | region_analyzer.py | `@@ -12948,49`（`_extract_with_items` EXTENDED_ARG 跳过 + 递归 `_parse_bind_unpack`） | ✅ | 递归产生式 target = Name | '(' 目标元组 ')' 与语法一一对应；槽位非 STORE_*/UNPACK_* 即 target=None（无 fallback 无猜测）；UNPACK_EX 位协议同 commit 2。 |
| 5 | region_ast_generator.py | `@@ -9834,6`（+260 行：`_B34C_CHAIN_STOP_OPS`/`_b34c_has_held_replace`/`_b34c_is_exit_window`/`_b34c_finally_deferred_return`） | ✅/⚠️ A7 | 判据链 R1 区域树归属（try_blocks + has_finally）/R2 逆向栈扫描（栈效应模型）/R3 链走查（budget 16 + visited + 退出窗口先剥后核 + held 替换拒收）全为结构事实；`budget 16`/`_B34C_CHAIN_STOP_OPS` 为预算与操作码集（非偏移魔数）；六段主注释在位。⚠️ `_b34c_has_held_replace`(:9864)/`_b34c_is_exit_window`(:9881) 缺 C1/C2/C3 条款（A7）。 |
| 6 | region_ast_generator.py | `@@ -47817,6`（`_generate_block_statements_body` B34c 接入点） | ✅ | 置于 `_try_deferred_return_in_loop` 之后；判据源唯一。 |

### A 项总裁定

| 项 | 裁定 | 依据 |
|---|---|---|
| A1 名字白名单 | **通过** | 全部判据无用户标识符/文件名/函数名字面量；`_const_code_is_async_comprehension` 的 `<listcomp>` 等为编译器合成名（声明在案）。 |
| A2 start_offset 魔法阈值 | **通过** | 无偏移魔数；`budget 16`/`_steps < 8`/arity 位掩码/SWAP argval==2/恰 3 None 均为协议或预算事实。 |
| A3 跨层读取（C1/C2） | **通过** | 判据链自底向上（块→链→区域归属），宿主定位在本层 regions/parent 链；junction ∈ with_blocks 显式禁跨区域链。 |
| A4 新增 self 跨方法状态 | **通过** | 四 commit core/ 增行 grep `self._x =` 零命中；`_b34b_reach` 等均为方法局部。 |
| A5 以少发射换全绿 | **通过** | 哨兵 OK.py 内容变化均为增行（显式 return None）/失败单元内变化，六哨兵读数全持平，无删输出绕过。 |
| A6 判据面 vs 声明 | **通过（1 项颗粒度记录）** | B30/B34b/B34c/B35/B33 判据面与 FIX.md 声明逐一比对一致；bare-None 去噪集颗粒度见上表 #3。 |
| A7 docstring 三要素 + C 条款 | **❌（4 方法）** | `_b31_continuation_owner`(:9278)、`_const_code_is_async_comprehension`(:9348)、`_b34c_has_held_replace`(:9864)、`_b34c_is_exit_window`(:9881) 缺 C1/C2/C3。 |
| A8 批次间一致性 | **❌（1 hunk）** | `4cd2a9f6 @@ -30717,9` 静默移除 LOOP_BACK_EDGE 跳过；其余跨 commit 演变（B32 因子化、B32 尾剥对、`_extract_with_items` 两次演进、`_detect_with_body_return` 改判）均有 FIX.md/注释声明。 |
| A9 插桩零残留 | **❌（2 hunk）** | `4cd2a9f6 @@ -695,7`/`@@ -767,7` 破坏性触碰既有 R23N21_DEBUG 插桩（删 import 留 print）；四 commit 未新增任何 print/探针；根目录 `_patch_dbg.py` 等 6 个临时驱动文件由 `30468033` 清理（✅）。 |
| A10 BOM | **❌（红线）** | region_ast_generator.py BOM 于 `fbfc2e7b` 剥除未恢复（现值 `222222`）；pattern_parser.py 无 BOM（✅ 该半项合规）。 |

---

## §2 读数复跑表（声明 vs 实测）

复跑方法：round6 16 文件先经 `pycdc.py -o` 再生成并 `diff` 确认与已提交 OK.py **逐字节 SAME**（零漂移），后 `pyc_verify.py batch`（报告落 `rounds/round6/r6_recheck.json`）；哨兵逐个再生成 + single。

| 验证面 | FIX.md/任务书声明 | 本轮实测 | 虚报判定 |
|---|---|---|---|
| round6 全量 16 文件 | 115/115 = 100%，16 success / 0 failure | **115/115 = 100%，16 success / 0 failure**（r6_01 8/8、r6_02 7/7、r6_03 7/7、r6_04 11/11、r6_05 6/6、r6_06 5/5、r6_07 6/6、r6_08 8/8、r6_09 8/8、r6_10 6/6、r6_11 6/6、r6_12 6/6、r6_13 8/8、r6_14 7/7、r6_15 8/8、n6_01 8/8） | **零虚报** |
| IQCommon/tools.pyc | 6/6 | **6/6 success** | 零虚报 |
| IQCommon/trade_schedule.pyc | 6/6 | **6/6 success** | 零虚报 |
| IQCommon/mq_connector.pyc | 13/13 | **13/13 success** | 零虚报 |
| 「strategy 2/2」 | 2/2 | **实测 = `IQCommon/strategy/strategy.pyc` 2/2 success**（FIX.md 简写「strategy」；任务书误写为 strategy_info_utils） | 零虚报（命名勘误见 §6） |
| IQCommon/util/strategy_info_utils.pyc | —（任务书标注 2/2） | **30/30 success**（该文件实为 30 单元全对，优于任务书标注；非虚报，系任务书文件名张冠李戴） | 记录 |
| IQEngine/utils/scheduler.pyc | 52/52 | **52/52 success** | 零虚报 |
| IQCommon/util/trade_info_utils.pyc | 36/41 = 基线；失败 = trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id；check_trade_name 不在失败列表 | **36/41 = 87.80%；失败 5 单元与声明逐一相符；check_trade_name 不在失败列表** | 零虚报 |
| fly/data/quotation.pyc（round5 哨兵） | 152/153，唯一失败 change_his_to_forward | **152/153；唯一失败 change_his_to_forward** | 零虚报 |
| round5 残留 rv5_23 | 8/10 | **8/10** | 零虚报 |
| round5 残留 rv5_24 | 8/9 | **8/9** | 零虚报 |
| round5 残留 rv5_25 | 11/12 | **11/12** | 零虚报 |
| （追加）option_account.pyc | R66 基线 100% | **35/35 success**（LOOP_BACK_EDGE 移除后无回归） | 通过 |
| OK.py 再生成漂移 | — | 16 支 round6 + 6 哨兵 + quotation + option_account 全部 **SAME**（`git status` 无 OK.py 变化） | 零回归信号 |

**§2 结论：FIX.md 全部读数声明经独立复跑零虚报；无任何 success→failure 位移。**

---

## §3 变体攻击表（7 探针 29 单元，全部为新构造，不与 r6_01..r6_15/n6_01 重复）

探针源码 `test_repros/round6/rv6_*.py`，pyc 为 Python 3.11 magic，OK 产物由 `pycdc.py -o` 生成后 `pyc_verify.py single` 实测。归因 = 修复前树（1d88bdbc worktree）重反编译输出与现树对比。

| 探针 | 攻击面（对应判据） | 单元 | MATCH | 判定 | 归因（修复前树对照） |
|---|---|---|---|---|---|
| rv6_01_asyncwith_threestate | B29/B32：async with 三态体（return/break/continue/raise）压入 try+for 双宿主 | 5 | 3 | **MISMATCH**（aw_break_in_try_for、aw_continue_in_try_for） | 修复前更差（裸 Expr + `await None(None,None)` 幻影 + `as` 丢失）→ 修复有增益但**未封闭 break/continue 态**：产物 if 反转 + break/continue 提出分支 + 幻影 `if True: pass`（既有缺口，B29 族残留）→ **B37** |
| rv6_02_outer_handler_boundary | B34b：内层 with 与外部 WITH_EXCEPT_START 处理器相邻的可达性反例（while 宿主、双层 with raise、for-else 含 with-break） | 4 | 2 | **MISMATCH**（outer_raise_catch：外层 with 内 `return 1` 上提出 with 且尾 `return 2` 丢失；nested_with_else_loop：幻影 `while False: pass` 复发） | 修复前缺 `return None`/裸 `y` → 修复有增益但未封闭（既有缺口）→ **B38** |
| rv6_03_bare_none_dual_form | B34b 细化判据双向：条件假边 bare-None 尾声 vs 无条件边 exit-block 同函数共存 | 4 | 4 | **MATCH**（两形态双向判定均正确） | 通过（双向形态实证补强 B34b） |
| rv6_04_finally_deferred_double | B34c：双层 try/finally 嵌套 + finally 覆写 return + finally 内嵌 finally×with | 4 | 1 | **MISMATCH**（三函数全败：`return xs[0]`→裸 `xs[0]`，`try_fin_fin_body_with` 另丢内层 finally 尾语句） | 修复前输出与现树**逐字节相同** → 修复未触及该深度，纯既有缺口 → **B39** |
| rv6_05_yieldfrom_mixed_else | B35：for-else 内 yield from + 三段交替双夹层 | 4 | 3 | **MISMATCH**（gen_for_else_mixed：`else: yield 0` 整体丢失，for-else 未发射） | 修复前线性夹层全丢、现树线性面（gen_three_alternate 等）已封闭 → 剩余为 for-else 宿主（既有缺口）→ **B40** |
| rv6_06_withitem_deep_async | B33：async def 宿主 withitem 深嵌套 `(a,(b,*c))`/`(a,*rest,z)`/`((a,*b),(c,d))` | 4 | 1 | **MISMATCH**（三函数全败：`async with mgr:` 裸 + 幻影 `b, *c = None` 等部分目标丢失） | 修复前裸 Expr + 幻影 if True → 修复有增益（return 恢复）但 async 宿主目标提取未封闭：`_extract_async_enter_chain_target`(:31503) 仍单名 STORE 假设，B33 递归解析未覆盖 async 入口链（既有缺口）→ **B41** |
| rv6_07_foreach_fused_return | B36-f：while-else 融合 return + 多语句 else + 双层循环 else | 4 | 4 | **MATCH** | 通过（B36-f 宿主无感实证补强） |
| **合计** | | **29** | **18** | 11 MISMATCH / 5 探针 | 11 失败单元全部为**既有缺口**（无修复引入回归） |

---

## §4 新破口登记（B37 起；全部经修复前树归因为既有缺口、本轮变体新暴露）

### B37 — async with 体 break/continue 态在 try+for 宿主下装配错序（P1）
- **锚点**：region_ast_generator.py `_generate_with` 体循环（:31757 起）——`aw_continue_in_try_for` 产物 `if x % 2: pass / else: out.append(v) / continue / continue / if True: pass`（if 反转 + 双 continue + 幻影守卫）；`aw_break_in_try_for` 同签名。
- **机制**：B29 封闭覆盖 return/raise 态（rv6_01 两态 MATCH）；break/continue 经 try 异常表切块后体块角色与 `_walk_async_pending_return`/升级判据不匹配，落入通用分支以 POP_JUMP 终结块路径重排。
- **最小复现**：`test_repros/round6/rv6_01_asyncwith_threestate.py::aw_break_in_try_for / aw_continue_in_try_for`。

### B38 — 外层 with 体尾 return 被内层 with 合并上提 + 尾部 return 丢失；for-else 含 with-break 幻影 while False 复发（P2）
- **锚点**：`_generate_with` 嵌套合并路径（`with m1, m2:` 扁平化时宿主边界归属）+ B34 幻影循环路径（`_loop_generate_for` else 摊平）。
- **机制**：outer_raise_catch 产物 `with m1, m2:` 后 `return 1` 落到 with 外、`return 2` 蒸发——双层 with 异常路径的 exit-block 归属把「内层 with 之后的语句」误归外层出口；nested_with_else_loop 为 B34 幻影 `while False: pass` 在「for-else 体含 with-break」宿主的复发（else 体发射正确，体侧幻影）。
- **最小复现**：`rv6_02_outer_handler_boundary.py::outer_raise_catch / nested_with_else_loop`。

### B39 — 双层 try/finally 嵌套下延迟 return 跨链重构失效（P1）
- **锚点**：`_b34c_finally_deferred_return`（region_ast_generator.py:9898）R1 归属判据——值块 owner 为**最内层** TryExceptRegion 时链走查在跨层（外层 finally 副本/第二 with 协议）处断裂返回 None，回退通用路径裸 Expr 化。
- **机制**：B34c 声明面为单层（try→finally 含 with / 嵌套 finally 单层）；双层 try/finally（`try: try: return X finally: ... finally: ...`）的值段归属与链形态均超出现判据，产物 `try: xs[0]`（return 剥除），`try_fin_fin_body_with` 另丢内层 finally 尾语句（`xs.append(2)`）。
- **最小复现**：`rv6_04_finally_deferred_double.py` 三函数（现树输出 = 修复前树逐字节相同）。

### B40 — for-else 宿主内「yield from + else: yield」的 else 体丢失（P2）
- **锚点**：`_generate_loop` is_yield_from_loop else 处理（B35 拆分判据）——for-else 的 else 块含 yield 语句时 else 体整体未发射（产物无 else）。
- **机制**：B35 封闭面为**线性连续 yield-from 夹层**（`yield from xs; yield 0; yield from ys` 现树 MATCH，三段交替 MATCH）；for-else 宿主下混合 else 块未被拆分判据覆盖（else 块产出为空而非混合形态）。
- **最小复现**：`rv6_05_yieldfrom_mixed_else.py::gen_for_else_mixed`。

### B41 — async with 宿主 withitem 元组/星号目标提取失效（P1）
- **锚点**：`_extract_async_enter_chain_target`（region_ast_generator.py:31503）——async 入口链目标提取仍为「出口块首条 STORE_* 单名」假设；`_extract_with_items` 的 B33 递归解析（region_analyzer.py:13072 起）未覆盖 BEFORE_ASYNC_WITH 入口链布局。
- **机制**：`async with mgr as (a,(b,*c))` 产物 = 裸 `async with mgr:` + 体首幻影 `b, *c = None`（首名 a 蒸发、其余目标 None 回填）；`(a,*rest,z)`/`((a,*b),(c,d))` 同签名。同步 with 深嵌套（r6_09.w_deep_unpack）与本轮 rv6_06 异步宿主形成同构对照——**B33 修复判据面窄于其声明的 withitem 全域**（声明「withitem 元组/星号目标」未限定同步）。
- **最小复现**：`rv6_06_withitem_deep_async.py` 三函数。

### 归属总表

| 编号 | 归属 | 证据 |
|---|---|---|
| B37/B38/B39/B40/B41 | 既有缺口（变体新暴露，非修复引入） | 修复前树（1d88bdbc worktree）重反编译输出：B39 与现树**逐字节相同**；B37/B38/B41 修复前更差（修复有正增益未封闭）；B40 线性面修复后封闭、for-else 宿主残留；round6 全量 115/115 + 六哨兵 + round5 残留零漂移背书「零回归」 |

---

## §5 打回项清单（打回必须列具体 hunk 与理由）

| # | 违反条款 | hunk/锚点 | 理由 | 修复要求 |
|---|---|---|---|---|
| 1 | **A10（G0 红线）** | `fbfc2e7b` region_ast_generator.py `@@ -1,4` | 剥除 BOM `efbbbf` 且四批修复+收官快照均未恢复（评审时点 4135e6db 实测在位） | 恢复 BOM 并纳入修复批次自测项（head -c 3 校验） |
| 2 | **A8** | `4cd2a9f6` region_ast_generator.py `@@ -30717,9`（现树 :31757 前） | 静默移除 `BlockRole.LOOP_BACK_EDGE` 跳过分支（R8/R66 两代判据），FIX.md/注释零声明、动机零论证；实测 option_account 35/35 无回归但程序违规成立 | 恢复该分支或以声明+回归实证（validate_data/option_account 哨兵）重新落地 |
| 3 | **A9** | `4cd2a9f6` region_ast_generator.py `@@ -695,7` / `@@ -767,7`（现树 :733/:803） | 删 `import sys as _sys` 留 `print(..., file=_sys.stderr)`：R23N21_DEBUG 插桩残留呈破损态 | 连同既有 R23N21_DEBUG 插桩一并清除或恢复 import（建议清除） |
| 4 | **A7** | `fbfc2e7b` 新增 `_b31_continuation_owner`(:9278)/`_const_code_is_async_comprehension`(:9348)；`30468033` 新增 `_b34c_has_held_replace`(:9864)/`_b34c_is_exit_window`(:9881) | 修复新增方法缺 C1/C2/C3 条款声明（spec：判据与注释不一致 = 评审不通过） | 补齐条款声明 |
| 5 | **B37–B41** | §4 五破口（11 单元） | 「With/AsyncWith + async 五件套」判据面在宿主结构/嵌套深度变体下仍有 5 族未覆盖形态；round6 全清 115/115 成立但**完备声明不可扩展至变体面** | 登记入台账交后续轮次； wiki 降格声明按 §4 修订 |

通容检查：以上各项均为任务书 A1–A10 明文检查项或变体攻击的直接产出，无自由裁量；其中 #1/#2/#3/#4 属修复工程师可在单一批次内机械修复项，#5 属登记推进项。**因 #1 为红线且 #2/#3 为合规硬伤，本轮终判为打回，不得以「读数全绿」通容。**

---

## §6 附注

1. **哨兵命名勘误**：任务书与 FIX.md 之「strategy 2/2」实为 `site-packages/IQCommon/strategy/strategy.pyc`（2/2 success 实测）；`site-packages/IQCommon/util/strategy_info_utils.pyc` 实为 30 单元、实测 30/30 success（Round 61 即已 30 单元全对）。两个哨兵均 100% MATCH、OK.py 与已提交版逐字节 SAME，无回归。
2. **复核产物清单**：`rounds/round6/r6_recheck.json`（round6 batch 报告）；`test_repros/round6/rv6_01..rv6_07`（源码 + pyc + OK 产物）。复核过程零修改 core/、parsers/、scripts/、pycdc.py、FIX.md/REVIEW.md/spec.md/tasks.md；未手改任何 `*OK.py`。
3. **正向确认**（打回不掩盖的成果）：四批修复对 115 单元全清读数真实成立；B29 封闭使 async with 体 return/raise 态获得宿主无感装配（rv6_01 return/raise 态、rv6_02 inner_with_outer_tail MATCH）；B36-f 在 while-else/多语句 else/双层循环 else 宿主下无感（rv6_07 4/4）；B34b bare-None 细化判据双向形态正确（rv6_03 4/4）；B35 线性多夹层封闭（rv6_05 三段交替 MATCH）；B33 同步宿主递归解析（r6_01/r6_09 全对维持）。判据面本身无白名单、无偏移魔数、无跨层读取、无新 self 状态——**算法方向合规，工艺与边界面不合规**。
