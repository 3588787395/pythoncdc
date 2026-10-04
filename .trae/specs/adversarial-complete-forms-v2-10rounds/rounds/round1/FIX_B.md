# FIX_B.md — Round 1.2 修复工程师位 B（接手者）落地报告

规范：`adversarial-complete-forms-v2-10rounds`（Round 1.2 修复批）
涉改文件：`core/cfg/region_ast_generator.py`（B71 前任在途接手 + B73/B75/B76）、`core/cfg/ast_generator_v2.py`（合规清理 ×2）、`core/cfg/structured_analyzer.py`（合规清理 ×1）
判据纪律：I.4 白名单（块末 opcode / 后继前驱集合 / 异常表 / 区域成员关系 / opname 序列同构 / code object 元数据）；无名字白名单、无魔数偏移、无跨层无守卫反查、无 self 新增跨方法状态、无硬编码深度上限。
禁令遵守：零 git commit；region_analyzer.py / code_generator.py / comprehension_generator.py 零改动；*OK.py 仅重生成零手改；test_repros 探针源码零改动。

**代码已落地**（落地标记 grep 证据：`_b75_consume_arm_return_copies`、`_is_finally_copy_return`、`_b75_try_arm_returns`、`_b75_handler_returns`、`_hard_reserved` 均在树中定义且被调用；B76 补发射块在 `_generate_boolop_impl` augassign 分支；见 §2–§5）。

---

## §0 接手核查

前任位 B 在途未提交工作经 `git diff` 逐 hunk 审查：[B71] B68 门控扩展（finally 体仅循环控制终结块）已在树中，r10_21 复测 **4/4** —— 补完确认，无遗留半成品；region_ast_generator.py 双核心 **BOM 恢复单头 efbbbf ×1**（round9 红线）字节级复核通过。前任遗留探针 `test_repros/round6/_cmpOK.py` 孤儿已删除。

## §1 B71 fin_continue/fin_break【已封闭·接手确认】

r10_21 **4/4 全 MATCH**（重生成 + pyc_verify 权威口径）。前任在途修复有效，本位仅验证与接手登记。

## §2 B76 augassign × BoolOp RHS 体蒸发【已封闭】

**破口**：rv10_32 v_aug_boolop_rhs——`x += a and b` 形态 AugAssign 封闭发射后 merge_block 中 STORE 之后的剩余指令（含 `return x` 的值装载 + RETURN）被吞，函数体蒸发。

**修复**（`_generate_boolop_impl` augassign 分支，补发射段）：AugAssign 只消费 merge_block 中 in-place `BINARY_OP` 之后的**首个** STORE_*；其后剩余指令经 `_downstream_region_entry`（F3 模式）派发下游区域，否则走「裁剪→补发射→还原」先例（R02/R78/P21 模式）：临时摘除 merge_block → `_generate_block_statements` 补发射 → 恢复原指令与 generated 标记。**读数：rv10_32 8/8**。

## §3 B65 链式赋值 × 嵌套 BoolOp【验证通过·零改动】

b6576_probe（链式赋值 × 嵌套 BoolOp RHS）重生成 + 验证 **4/4 全 MATCH**。前任实现有效，无需改动。

## §4 B73 try 四段 import 宿主泄漏【已封闭】

**破口**：r10_04 imp_try_sections——finally 体含条件段时，handler 内 `return fb(str(e))` 的 return 路径存在**第三副本**（finally 条件段副本，块 162 = IMPORT_NAME m6 清理链 + RETURN_VALUE）。`_find_return_chain_via_successors` 的 `_is_cleanup_with_return` 白名单缺 IMPORT_NAME/IMPORT_FROM，BFS 在副本块断链 → return 被剥成裸 Expr + 副本体泄漏。

**修复**（取证 `probes_fixB/diag_b73.py`）：新增闭包 `_is_finally_copy_return(b)`——候选块 RETURN 终结，且其前缀 opname 序列与某 has_finally 区域的 finally 异常副本体序列（剥 PUSH_EXC_INFO 头 + RERAISE/COPY/POP_EXCEPT/SWAP 尾）指令级同构，且块 ∈ 该区域 blocks 但不在 try/finally 本体集合。以同位接入 BFS（选择加判据而非扩白名单：避免误吸收含用户语句的任意块）。命中后既有 leftover 机制自动重建 `Return(expr)` 并标记 generated。**读数：r10_04 3/3**（`return fb(str(e))` 正确、无副本泄漏）。

## §5 B75 try 宿主 global 声明 5/6→6/6【已封闭】

**破口**：r10_15 g_in_try_except——try 主臂 `return CACHE[key]` 与 except 臂 `return None` 穿过 finally 条件段副本（CPython 3.11 为每条臂内 return 复制一份条件段副本：try 主臂副本 [72,86,140]、except 臂副本 [164,178,234]），既有发射把副本当真实 if/else 注入两臂（幻影双臂）并剥除臂 return（值块降级裸 Expr `CACHE[key]`）。

**前置事实（实验证实）**：global 声明在 global-read + STORE_SUBSCR 形态下对 co_code **零影响**（`.__code__.co_code` 逐字节一致）——B75 字节码失败完全来自 return/副本归属，模块层 `global LOG, CACHE` 发射为登记在册的惰性噪声（源码质量问题，非本轮判据目标）。

**修复**（取证 `diag_b75.py` 块布局 / `diag_b75b.py` 判定链回放 / `diag_b75c.py` 全驱动插桩，历三重障碍）：
1. **前置归约** ` _b75_consume_arm_return_copies(region)`（六项模板 docstring）插在 `_generate_try` 头部（handler 块快照**之前**，使副本块标记计入 `_pre_consumed_*` 免遭集合差回退撤销）。候选扫描 = IfRegion ∧ 块全 ∈ region.blocks ∧ 避开硬保留集 ∧ 避开其他 TryExceptRegion ∧ `_exc_seq` 前缀同构 ∧ RETURN 终结块。
2. **障碍一（JUMP_FORWARD 守卫）**：try 臂值尾块（块 48）以「无条件前跳进副本段」收尾，原守卫无条件拒绝 JUMP* 前驱 → 改为先剥离**指向副本段**的 JUMP_FORWARD/JUMP_ABSOLUTE 再判值尾（目标不在副本段或剥离后残留 JUMP* 仍拒绝）。值尾经 `expr_reconstructor.reconstruct` 重建 → try 臂 Return。
3. **障碍二（_reserved 拆分）**：取证发现副本块已被分析器归入 `try_blocks=[...,72,86,140]` 与 handler `hbs=[...,164,178,234]`，原「避开全部法定归属」判据致全 SKIP → 拆分 `_hard_reserved`（仅 finally_blocks ∪ else_blocks ∪ handler_entry_blocks ∪ cleanup_blocks），try_blocks/handler 块改为合法消化宿主。
4. **障碍三（dict `**` int 键）**：瞬态属性挂载误用 `**{int_key: ...}` 展开（TypeError: keywords must be strings，异常被 generate() 吞掉致函数体 Pass）→ 改普通 dict 合并。
5. **两臂认领**：副本段块整体标记 generated + `_generated_regions.add`；try 臂 Return 挂 `region._b75_try_arm_returns`（键=值尾块偏移，`_generate_try_body` 块循环顶认领）；except 臂 Return 挂 `region._b75_handler_returns`（键=handler 入口偏移，回溯透明链至 CHECK_EXC_MATCH 定位，值=段终块 RETURN 前装载尾、无则 Constant None，handler 循环尾认领）。任一重建失败整体放弃（C3 不半应用）。

**读数：r10_15 6/6**（g_in_try_except = try 臂 `return CACHE[key]` / except 臂 `return None` / finally 臂 `if CACHE: LOG.append(key)`）。

## §6 合规清理【已完成】

| 位置 | 清理内容 | 替代 |
|---|---|---|
| ast_generator_v2.py（原 :9049） | `[临时调试] 硬编码跳过 offset 62` 整段删除 | —（临时插桩残留） |
| ast_generator_v2.py（原 :14990） | 魔数 `start_offset == 74` no-op 删除 | —（死代码） |
| structured_analyzer.py（原 :14330） | `depth > 3` 硬编码深度上限 | 结构判据：with-as 目标 STORE 装配在 BEFORE_WITH 后**线性框架链**（单后继块）；多后继 = 已进入 with 体控制流（分支位）停止下探；终止性由 visited 防环保证 |

清理后 with 类探针回归：r6_01 8/8、r6_03 7/7、r6_09 8/8、r6_11 6/6 —— 行为等价。

## §7 读数表

**目标锚点（全部转 MATCH）**：

| 探针 | 前 | 后 |
|---|---|---|
| r10_21（B71） | 2/4 | **4/4** ✓ |
| rv10_32（B76） | 7/8 | **8/8** ✓ |
| b6576_probe（B65） | 4/4 | **4/4** ✓（验证） |
| r10_04（B73） | 2/3 | **3/3** ✓ |
| r10_15（B75） | 5/6 | **6/6** ✓ |

**负对照（14 文件 + 4 with 宿主，全 MATCH）**：n6_01 8/8、n7_01 5/5、n7_02 5/5、n8_01 4/4、n8_02 5/5、n9_01 3/3、n9_02 4/4、n10_01 2/2、n10_02 2/2、n10_03 2/2、n10_04 3/3、rv9_03 4/4、rv10_31 13/13、rv10_33 6/6；r6_01 8/8、r6_03 7/7、r6_09 8/8、r6_11 6/6。

**站桩五行（复用 r1_sentry_index.json / r1_replay_index.json）**：

| 行 | 本轮读数 | 基线 | 判定 |
|---|---|---|---|
| round6 | 115/115 | 115/115 | 持平 ✓ |
| round7 | 124/143 | 108/128 | 上升（位 A 联修 B50/B46/B74 增益；REGRESSED=0 由 34 集背书） |
| round8 | 129/138 | 110/118 | 上升（同上） |
| round9 | 62/64 | 50/50 | 净上升；2 个 MISMATCH 为存量（见 §8 归因） |
| 哨兵 site-packages | 302/308 | 302/308 | 持平 ✓ |

**34 小测试集（权威 pyc_verify.py）**：**1505/1568，REGRESSED=0**（与位 A 权威读数持平；quotation 152/153；33 文件残留失败名单与基线一致）。产物：`fixB_small34_pycverify.json` + `fixB_small34_index.json`。

**IV.2 门禁自检**：BOM 单头 ×2（region_ast_generator.py / region_analyzer.py 各 efbbbf ×1，字节级）；插桩残留 grep = 0；IMPORT_OK ×3；COMPILE_OK ×3 —— **PASS**。

## §8 降级 / 未竟登记

| 项 | 状态 | 说明 |
|---|---|---|
| rv9_01_b68_nonfin_tail 4/5 | 存量缺口（非本轮引入） | stash A/B 归因：HEAD 版本重生成读数同为 4/5 |
| rv9_02_b66_with_nest 4/5 | 存量缺口（非本轮引入） | 同上，HEAD 复测 4/5 |
| round7/8 站桩单元总数漂移（128→143 / 118→138） | 口径注记 | verify single 交集口径随 OK 产物函数集变化；回归判据唯一 = 34 集 REGRESSED=0 |
| 模块层 `global LOG, CACHE` 惰性发射 | 登记在册 | global 声明字节码零影响已实验证实；属源码质量项非字节码判据项 |
| docstring 六项模板 | 本位触及方法已覆盖 | `_b75_consume_arm_return_copies`（六项全）、`_find_return_chain_via_successors`（六项补齐）；B76 发射段行内注释；更外层存量方法非本位触及面 |

## §9 产物清单

- `rounds/round1/probes_fixB/`：diag_b73.py、diag_b75.py、diag_b75b.py、diag_b75c.py、b6576_probe.pyc/+OK.py、fixB_probe_results.json（机器可读版）
- `rounds/round1/`：fixB_small34_index.json、fixB_small34_pycverify.json
- regen 产物：r10_04OK / r10_15OK / r10_21OK / rv10_32OK / rv10_31OK / rv10_33OK / b6576_probeOK + 负对照 14 文件 OK + 站桩全量 OK + 34 集 site-packages 34 个 *OK.py（均为重生成，零手改）
- 删除孤儿：test_repros/round6/_cmpOK.py
