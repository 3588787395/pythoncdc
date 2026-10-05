# Round 2 复核报告（Task 2.3 复核工程师）—— 修复批次 P2+P3 终审

- 复核角色：独立对抗审计（只读 core/，独立复跑，变体攻击；除本报告外零写入，零 git 提交）。
- 受审对象：`git diff 87e59c49..fd04c276 -- core/`（P2 = de039b80 位 2 + 在途 3a9db846 + P3 = fd04c276），4 文件 +1255/−22 行，33 hunk 逐 hunk 全读。
- 工具链：`D:/Python/python.exe`（3.11.7）→ `pycdc.py <pyc> -o <OK.py>`（先 regen 后 verify，RV2 方法学）→ `scripts/pyc_verify.py single <pyc>`。
- 工作树状态：复核全程跟踪文件零修改；全量 regen（42 探针 + 45 站桩）后 `git status --porcelain` 零变化（修复侧 OK.py 产物字节级可复现，确定性实证）。

---

## §0 终判

## **打回**（窄口径：算法内容与读数全部通过，违反 spec 理论基准 I 的 I.5 一条硬性条款 + I.7 部分缺口）

| 项 | 判定 |
|---|---|
| A. 逐 hunk 合规（I.4/I.3/I.6/BOM/插桩） | 通过（1 项 I.5 违反除外，见 §1.1） |
| B. 独立复跑（42 探针/45 站桩/34 集/字节影响面） | **全部与修复声明逐位一致，零虚报** |
| C. 变体攻击（7 探针） | 无回归（基线 MATCH→现 FAIL = 0）；2 变体改善（rv3_03/rv3_05）；新登记 5 组存量族外推证据（§4） |
| D. I.5 命名前缀 | **违反**（新方法 `_merge_annassign_statements`，零容忍条款命中） |
| E. I.7 docstring 六项模板 | 部分缺口（4 个触及的 `_generate_*` 方法未补齐） |

**打回理由与机制**：spec.md 理论基准 I 章头标注「强制性，违者评审零容忍打回」，其下 I.5 明文「禁止方法命名前缀：`_fix_ / _merge_ / _patch_ / ...`（新增方法不得使用）」。

- **锚点**：`core/cfg/region_ast_generator.py:32776`（`def _merge_annassign_statements`，3a9db846 引入）；调用点 `:32671`、`:50754`。
- **违反条款**：I.5（新增方法不得使用 `_merge_` 前缀）。既有豁免仅覆盖存量 `_merge_block_is_*`（region_ast_generator.py:19700/:39849），本方法为全新增。
- **机制**：B85 AnnAssign 归并修复以 `_merge_` 开头命名新方法，落入禁止前缀字面集合。同时暴露**自检口径缺口**：FIX_P2 §门禁5 与 FIX_P3 §门禁5 的禁止前缀 grep 均只列 `_fix_|_patch_|_fallback_|_hack_|_workaround_|_temp_` 六项、**遗漏 `_merge_`**，导致自检放行；FIX_P3「新增方法 0」声明仅对其自身基线（3a9db846..fd04c276，+82 行纯守卫）成立，对批次整体（87e59c49 起共 9 个新方法/新类）不成立，报告口径未加说明。
- **补救（机械性，无需重审逻辑）**：重命名 `_merge_annassign_statements` → 非禁止前缀名（如 `_annassign_pair_merge` / `merge_annassign_statements_pair`，3 处：def + 2 调用点）；I.7 缺口按 §1.3 清单补 docstring；FIX 模板自检 grep 补 `_merge_` 项。**除名 i.5/i.7 外，本批复核全部实质项（读数、封闭性、回归面、影响面）均通过，整改后无需重跑 42 探针全量，仅需名 i.5 重命名文件 smoked + 站桩抽验。**

---

## §1 逐 hunk 合规审查表（对照 spec 理论基准 I）

### 1.1 红线扫描（对 diff 新增行）

| 红线 | 扫描 | 命中 | 判定 |
|---|---|---|---|
| I.4-① 名字白名单 | grep `co_filename\|__name__ == '\|\.pyc'\|test_repros\|round[0-9]`（新增行） | 0 | **PASS** |
| I.4-② start_offset 魔数 | grep `start_offset [<>]=? \d{2,}`（新增行） | 0 | **PASS** |
| I.4-③ 跨层反查 | grep `\.entry in .*\.blocks`（新增行） | 1 处（B87 中间循环守卫 `r.entry in set(_lr.blocks) and _lr.entry in set(region.try_blocks)`，region_ast_generator.py:27401-27403 邻域） | **PASS**（区域成员关系双向包含，I.4 白名单明列「区域成员关系」；同层区域对，非跨层反查；与评审基线 14 处存量同类判据口径一致） |
| I.4-④ self 新增跨方法状态 | grep `self\.\w+ =`（新增行） | 仅 `_ChainAwareStoreDelegate.__init__` 的 `self._gen/self._block/self._chain_consumed`（:59 类内） | **PASS**（委托实例每次认领新建即弃、消费集作用域=单块认领，非 RegionASTGenerator 的 self 跨方法状态；docstring 已声明口径） |
| I.4-⑤ 少发射/深度上限 | grep `depth > \d\|MAX_DEPTH\|max_depth = \d`（新增行） | 0 | **PASS**；专项核对：B85 链归约/B89 trim 均带回退分支（判据不命中=原路径），B91 剥离仅作用于类体作用域且函数边界封闭——无以少发射换绿证据（站桩 45/45 持平 + 42 探针全量复跑佐证） |
| I.3 封闭守卫 | 逐守卫核对 | B87×2/B89/B85×4/B86/B91/B92/B84×3/B95/SWAP 尾段/finally 签名 argval 化 | **PASS**（全部为结构判据+显式回退的封闭守卫，无个案补丁、无生成层深度特判；逐守卫明细见 §1.2） |
| I.5 禁止前缀 | grep `_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_`（新增行） | **4 行，全部为新方法 `_merge_annassign_statements`（:32776 def + :32671/:50754 调用 + docstring 行）** | **FAIL → 打回项**（见 §0） |
| I.6 落地声明 | grep FIX 文档全部落地标记 | `_is_inside_intermediate_loop`、`_nr_is_ancestor`、`_bo_chain_jump_targets`、`_convert_formatted_value_expr`、`_render_format_spec_source`、`_convert_comprehension_object_call`、`parse_comprehension_code_object`、`_scan_prefix_chain_assign`（5 调用点）、`_merge_annassign_statements`（2 调用点）、`_b86_complete_with_items(region)`（:33792）、`_b89_trim_trailing_at_cond_jump`（5 调用点）、`_b91_strip_phantom_returns`、`_rag_is_pure_exception_protocol_block`、`_comp_delegate_for_block`、`_take_assert_prefix_stmts`/`_collect_await_protocol_chain`/`_reconstruct_await_block_stmts`（树中实存且被调用） | **PASS**（全部落地标记 grep 实存且接线；m12 3/3、x04 6/7、c11 10/10、x09 10/10 等读数为落地实证） |
| BOM 单头 | `head -c 3` 两核心文件 | region_ast_generator.py / region_analyzer.py 均 = `efbbbf` 且全文计数 = 1 | **PASS** |
| 插桩 | grep `print(\|breakpoint(\|import pdb\|pdb.set_trace`（新增行） | 0 | **PASS** |
| 临时文件 | fd04c276 vs 3a9db846 的 .trae/ 增删 | 删除 58 个 tmp_*，新增仅 FIX_P3.md + p3_probe_final.json + p3_regress_final.json；工作树 round2/tmp/ 空 | **PASS**（FIX_P3 §6.8 清理声明属实） |

### 1.2 逐守卫封闭性核对（I.3/I.4 实质审查）

| 守卫/hunk | 文件:行（约） | 判据类型 | 封闭性判定 |
|---|---|---|---|
| [B87] 嵌套预生成早退守卫 | region_ast_generator.py:3906-3927 | `_generated_regions`/`_generating_regions` 登记 + entry 已生成事实 | 封闭 ✓（「已完整生成」的唯一可信事实=区域生成器登记；C3 显式） |
| [B87] 中间循环宿主守卫 `_is_inside_intermediate_loop` | :27391-27405 | 双向区域成员关系（内层 entry ∈ 中间循环 blocks ∧ 循环 entry ∈ 本 region try_blocks） | 封闭 ✓（发射改由循环走查完成，非少发射；docstring [B87] 条目已追加） |
| [B87] handler 臂祖先豁免 `_nr_is_ancestor` | :29658-29672 | parent 链 + 块集成员 | 封闭 ✓（共享块集事实 vs 生成认领区分；C1/C3 明确） |
| [B87] finally 副本签名 argval 化 | region_analyzer.py:12157-12164/:12249-12261 | 指令 (opname, argval) 对 + 终结 opname 取首元素适配 | 封闭 ✓（签名端与匹配端同口径；rvC_v1..v4/v_b71 复测逐位一致佐证） |
| [B89] 链跳转目标排除 `_bo_chain_jump_targets` | :37352-37378 | 链块末跳转 argval 集合成员 | 封闭 ✓（外层操作数改由末尾 fall-through 发射，归属唯一非删除） |
| [B89] 尾随条件跳转修剪 `_b89_trim_trailing_at_cond_jump` | :33400-33490 + 5 调用点 | 首个条件跳转截断 + 末终结符后纯值生产后缀截断 | 封闭 ✓（带回退：无条件跳转/完整语句切片逐位保持；**变体 rv3_07 实证未过度修剪完整 if 语句**，见 §4） |
| [B85] 链式赋值前瞻归约 `_scan_prefix_chain_assign` | :32695-32774 + 3 路径接线 | COPY(arg=1) 复制边界 + [COPY+STORE]*/STORE 前瞻 + 值切片无终结符 | 封闭 ✓（目标数 <2 / 值非单一表达式 / FunctionDef 值均回退 None=原路径；三条语句重建路径同判据同语义，C2） |
| [B85] AnnAssign 归并（**I.5 违反载体**） | :32776-32850 | 相邻 Assign + `__annotations__['K']` 登记 Subscript 同名键 | 封闭 ✓（判据为同层语句结构事实；**命名违规另记**） |
| [B85] 推导式认领委托 `_ChainAwareStoreDelegate` | :59-97/:52834 | 拦截 `_build_store_statement` 单入口 + 同源链判据 | 封闭 ✓（不命中逐字节回落本体；消费集=认领局部） |
| [B86] with items 补全 `_b86_complete_with_items` | :33400-33590 | BEFORE_WITH 块内 opcode 形态 + 子区域块集排除 + 指令同一性去重 | 封闭 ✓（无候选链零改动；UNPACK 等复杂绑定保守回退） |
| [B86] 幻影协议块守卫 `_rag_is_pure_exception_protocol_block` | :50569-50615 + :50740 | 块内 opcode 全协议集 + 特征码必含 | 封闭 ✓（含任何用户值生产/存储即否定；不命中逐位不变） |
| [B84] AssertRegion 前导段消费 | :1948-1966 | AssertRegion 类型 + 既有 `_take_assert_prefix_stmts` 契约收口 | 封闭 ✓（:829/:877 既有 take 点同构，本处补顶层循环缺失 take） |
| [B84] DELETE_* 归约 + as-var 清理三元组 | :32184-32211/:32190-32206 | opcode 事实 + argval 同名三元组 | 封闭 ✓（与 `_generate_block_statements` R19N3 判据同构，C2 两路径同语义） |
| [B91] 类体幻影 return 递归剥离 `_b91_strip_phantom_returns` | :3702-3772 | 类体宿主 Return 语法非法 ⇒ 全部为幻影 + 函数边界不下探 | 封闭 ✓（宿主作用域封闭；无 Return 类体逐位保持——语句树未变时保持原节点，c14 实测注记在案） |
| [B92] LOAD_CLASSDEREF 值位回退 | :56396-56410 | 值指令全为加载类 opcode | 封闭 ✓（含非加载指令维持 None，不臆造语义） |
| [B95] await 挂起链 owner 语句性发射 | :8824-8853 | `_collect_await_protocol_chain` 后继/前驱 opcode 结构 | 封闭 ✓（非链 owner 行为逐位不变；复用 `_reconstruct_await_block_stmts` 单一事实源） |
| [位2移交] SWAP 尾段守卫 ×2 | :32538-32544/:32617-32636 | SWAP(2)+POP_TOP+RETURN 序 + RETURN 前剥除 SWAP/COPY/POP_EXCEPT/PUSH_EXC_INFO | 封闭 ✓（镜像 `_generate_block_statements_body` 既有 RC2 判据，C2） |
| [B90] spec 源码化 + 裸 FV 包裹 | ast_converter.py:1481-1567 | 节点类型字段三态 + 回退 `_convert_expression` | 封闭 ✓（未识别形态回退既有路径，无静默吞） |
| [B96] ComprehensionObject 还原 + co_flags 剥除 | ast_converter.py:1286-1348/:1764-1800 + comprehension_generator.py:79-113 | co_name 编译器合成名 + 恰一位实参 + co_flags&0x80 | 封闭 ✓（同步推导式保留 Await 包裹，C3 显式；解析失败回退原路径） |

### 1.3 I.7 docstring 六项模板核对（触及方法逐个）

| 方法 | 六项 + C1/C2/C3 | 判定 |
|---|---|---|
| ast_converter: `_convert_formatted_value_full` / `_convert_formatted_value_expr` / `_render_format_spec_source` / `_convert_comprehension_object_call` / `_convert_call_full` / `_convert_await_expr_full` | 齐全且与代码一致 | PASS |
| comprehension_generator: `parse_comprehension_code_object` | 齐全且与代码一致 | PASS |
| region_analyzer: `_collect_finally_body_blocks`（新增完整 docstring） | 齐全（①-⑥ + [B87] 条目 + C1/C2/C3） | PASS |
| region_ast_generator: `_generate_try` | 齐全 | PASS |
| region_ast_generator: `_generate_try_body` | 仅追加 [B87] 条目 + C 条款，**缺 ①②④⑤⑥ 模板标注** | **缺口**（FIX_P3 §4 声明口径为「追加条目」，未达 I.7 全模板） |
| region_ast_generator: `_generate_region`（B87 早退守卫触及） | 既有旧式 docstring，未补六项/[B87] 条目（守卫说明以代码内注释承载） | **缺口** |
| region_ast_generator: `_generate_with`（B86 补全调用触及） | 既有旧式 docstring，无 [B86] 条目（说明以调用点注释承载） | **缺口** |
| region_ast_generator: `_generate_block_statements_body`（B85/B92/SWAP 触及） / `_generate_block_statements`（B86 幻影漏斗触及） | 旧式 docstring，六项以 hunk 内注释块承载 | **缺口** |
| 新方法 `_scan_prefix_chain_assign` / `_merge_annassign_statements` / `_comp_delegate_for_block` / `_b86_complete_with_items` / `_b89_trim_trailing_at_cond_jump` / `_b91_strip_phantom_returns` / `_rag_is_pure_exception_protocol_block` / `_ChainAwareStoreDelegate` | 六项 + C 条款齐全（非 `_identify_*`/`_generate_*` 命名，仍主动补齐） | PASS（超额合规） |

**I.7 定性**：注释与代码行为**一致**（不触发「注释与代码行为不一致 = 评审不通过」条款），但 5 个触及的 `_generate_*` 方法未达六项模板字面要求。并入打回整改清单。

---

## §2 独立复跑读数表（RV2 方法学：先 regen 后 verify；与修复声明逐项对照）

### 2.1 42 探针（独立复跑 vs FIX_P3 声明）

| 探针 | 复核复跑 | FIX_P3 声明 | 同/异 |
|---|---|---|---|
| c01 | 5/5 MATCH | 5/5 | 同 |
| c02 | 6/7 | 6/7 | 同 |
| c03 | 3/4 | 3/4 | 同 |
| c04 | 5/6 | 5/6 | 同 |
| c05 | 5/5 MATCH | 全 MATCH | 同 |
| c06 | 3/4 | 3/4 | 同 |
| c07 | 5/6 | 5/6 | 同 |
| c08/c09 | 8/8、6/6 MATCH | 全 MATCH | 同 |
| c10 | 8/8 MATCH | 全 MATCH | 同 |
| c11 | **10/10 MATCH** | 10/10 | 同 |
| c12 | 3/3 MATCH | 全 MATCH | 同 |
| c13 | 2/3 | 2/3 | 同 |
| c14/c15 | 7/7、3/3 MATCH | 全 MATCH | 同 |
| m01 | **5/5 MATCH** | 5/5 | 同 |
| m02 | 2/3 | 2/3 | 同 |
| m03–m06 | 0/1 ×4 | 0/1 | 同 |
| m07 | **1/1 MATCH** | 1/1 | 同 |
| m08 | **2/2 MATCH** | 2/2 | 同 |
| m09 | 0/1 | 0/1 | 同 |
| m10/m11 | 6/6、1/1 MATCH | 全 MATCH | 同 |
| m12 | **3/3 MATCH（COMPILE_OK）** | 3/3 | 同 |
| nm01/nm02/nc01/nc02/nx01 | 全 MATCH | 全 MATCH | 同 |
| x01 | 4/7 | 4/7 | 同 |
| x02 | 5/7 | 5/7 | 同 |
| x03 | 6/7 | 6/7 | 同 |
| x04 | **6/7** | 6/7 | 同 |
| x05 | 6/7 | 6/7 | 同 |
| x06 | 7/7 MATCH | 全 MATCH | 同 |
| x07 | 4/4 MATCH | MATCH | 同 |
| x08 | 5/8 | 5/8 | 同 |
| x09 | **10/10 MATCH** | 10/10 | 同 |
| x10 | 2/3 | 2/3 | 同 |
| **合计** | **172/196** | **172/196** | **同** |

P2 声明里程碑亦复核成立：m12 COMPILE_OK（3/3）、x09 8/10→10/10（B96 位 2 + B95/SWAP 位 3 接力）。

### 2.2 站桩回归面（45 文件**全量**复跑，任务要求 ≥20 抽验）

全部 45 文件读数与 r2_regress_replay.json 基线**逐位一致、失败单元逐一相同**：

- 修复面 r10_04(3/3)/r10_06(3/3)/r10_14(7/7)/r10_15(6/6)/r10_16(7/7)/r10_21(4/4)、rv10_31(13/13)/rv10_32(8/8)/rv10_33(6/6)、r7_03(7/7)/r7_07(7/7)、rv8_01(7/7)、r8_06(10/10)：全 MATCH ✓
- 存量失败面 r7_08(7/8)、rv8_02(6/7)、v_b46(1/4)、v_b71(3/4)、v_b73(2/3)、v_b74(3/4)、v_b75(1/3)、rvC_v2(1/2)：同读数 ✓
- 负对照 n6_01(8/8)/n7_01/n7_02/n8_01/n8_02/n9_01/n9_02/rv9_03/n10_01..04：全 MATCH ✓
- v_b50(4/4)/v_b65(3/3)/v_b76(4/4)/rvC_v1/v3/v4：全 MATCH ✓
- 34 集抽验（6 文件全跑）：email_utils 3/4、cgroup_utils 7/8、executor 9/10、strategy_universe 10/11、trading_dates_mixin 13/14、realtime_event_source 12/13 —— 与声明逐位一致 ✓（任务指定抽验 email_utils 3/4、executor 9/10 成立）

### 2.3 字节级影响面抽验

| 抽验项 | 方法 | 结果 | 判定 |
|---|---|---|---|
| 非目标探针 c05、x06 | `git diff 87e59c49..fd04c276` 两文件 | **零差异（逐字节不变）** | 与 FIX_P2「其余 84 份逐字节不变」一致 ✓ |
| 全链 OK.py 变化面 | 分批次 `git diff --name-only` | P2 提交（de039b80）未含 OK.py 变化；在途（3a9db846）12 份（c01/c06/c11/c13/m01/m02/m07/m08/m12/x09 + 2 杂散）；P3（fd04c276）5 份（c04/m09/m12/x04/x10）+ v_b71_faceOK | 变化文件全部可归因已封闭破口（B84/B85/B86/B87/B88/B91/B92/B89/B90/B95），无未解释漂移 ✓ |
| 确定性 | 复核全量 regen 42+45 文件后 `git status` | 跟踪文件零变化 | 修复侧读数字节级可复现 ✓ |

**复跑总判：零虚报、零不符项。**

---

## §3 变体攻击结果表（7 探针，rv3_* 前缀，源码/.pyc/OK.py 在 `test_repros/round2/`）

回归判据：同形态在 87e59c49 基线 MATCH 而终态 FAIL 才算回归。基线复跑环境 = `git archive 87e59c49`（core+pycdc+scripts+bytecode）独立目录。

| 变体 | 形态 | 87e59c49 基线 | fd04c276 终态 | 判定 | 失败单元与机制注记 |
|---|---|---|---|---|---|
| rv3_01_b87_try_loop_mix | 三层嵌套 try 混合宿主（try→for→try→while→if→try）+ handler 臂 return | 2/3 FAIL | 2/3 FAIL | **存量同态，无回归** | `deep_try_nest`：finally 体 `total += 100` 副本泄漏进 handler 臂（`except ValueError: total += 100; return -1`）+ 幻影 continue——finally 内联副本归属错位（B87 变体三/B83 族外推）；**守卫未误伤**：合法深层 try 链语句序与体完整 |
| rv3_02_b89_boolop_chain | 模块级混合 boolop 链 `X = A or (B and C)`、`Y = (A or B) and C` 等 5 形 | 0/1 FAIL | 0/1 FAIL | **存量同态，无回归** | `<module>`：`Y = (_A or _B) and _C` → `Y = _A or _B or _C`（分组结构丢失、外层 and 链展平为 or）——分组 boolop 保真破口变体，B89 封闭仅覆盖「外层操作数并入内层组」子型，分组识别本身未覆盖「内层 or + 外层 and」模块根形态。**建议登记 B98（或 B89 族延伸），移交后续轮**。锚点：`_build_grouped_boolop_expression` 分组检测判据（region_ast_generator.py:37176 起） |
| rv3_03_b85_b86_func_domain | 函数域链式赋值 + 多上下文 with（守卫域外推） | 1/3 FAIL | **2/3 FAIL** | **改善（B85 函数域收益），无回归** | `chain_assign` 转 MATCH（B85 三路径同判据外推成立）；残余 `multi_with` Different bytecode（`with _os.popen(...) as fc, _os.popen(...) as fd:` 函数域第二上下文残余，存量族） |
| rv3_04_b91_class_match | 类体 match 真 guard（`if val:`）与假 guard（`if 0:`）各一 | 3/4 FAIL | 3/4 FAIL | **存量同态，无回归** | MatchTrueGuard MATCH（B91 主体封闭在真 guard 形态成立、可编译）；`MatchFakeGuard` 主体错构：`match val:` → `match __name__:`、`case 1 if 0:` → `case 1 as val:`（subject 提取错 + 假 guard 丢弃 + 臂体蒸发）——类体 match 装配族（B59-61/B81）新证据 |
| rv3_05_b92_classderef_shadow | 类体 LOAD_CLASSDEREF 读取 + 同名局部遮蔽（方法参数同名） | 5/9 FAIL | **9/9 MATCH** | **修复收益（B92 封闭外推成立）** | — |
| rv3_06_b87_with_for_else_arm | try→with→for→while 混合 + try-else 臂 + handler 臂 break | 1/2 FAIL | 1/2 FAIL | **存量同态，无回归** | `outer`：双重机制——(a) handler 臂 `break` 蒸发（**B97 已登记移交项的又一独立实证**）；(b) 内层 `while len(acc) < 2` 折叠为 `if`（循环头/回边判定，B94 邻域外推）。try-else 臂与 with/for 合法发射未受守卫误伤 |
| rv3_07_b89_trim_overtrim | 三元赋值后跟完整 if/比较语句（_b89_trim 过度修剪攻击） | 3/4 FAIL | 3/4 FAIL | **存量同态，无回归；trim 守卫无罪** | `ternary_then_if`/`ternary_then_cmp` 全 MATCH——**完整 if 语句未被 trim 误删，§1.2 识别的过度修剪风险实测未触发**；残余 `ternary_chain_then_while`：`b = (4 or 5) and 6 if d else 7` 重建差异，与 rv3_02 同为分组 boolop 保真族（非 trim 机理） |

**变体总判**：回归 = 0；修复收益 = 2（rv3_03 B85 域外推、rv3_05 B92 域外推）；新登记外推证据 = 4 组（rv3_02 分组 boolop 保真、rv3_04 类体 match subject 错构、rv3_01 finally 副本泄漏进 handler 臂、rv3_06 handler break + while 折叠），全部为存量族延伸、移交后续轮。

---

## §4 遗留观察（移交清单）

1. **【打回整改项】I.5 重命名**：`_merge_annassign_statements`（region_ast_generator.py:32776 def，:32671/:50754 调用）→ 非禁止前缀名；同步修复 FIX 报告门禁自检 grep 遗漏 `_merge_` 的口径缺口。
2. **【打回整改项】I.7 补齐**：`_generate_try_body`（补 ①②④⑤⑥ 标注）、`_generate_region`、`_generate_with`、`_generate_block_statements(_body)`（补六项模板或至少 [B84]/[B85]/[B86]/[B87]/[B92]/[SWAP] 触及条目 + C 条款，现仅有 hunk 内注释承载）。
3. **【建议登记】分组 boolop 保真破口（rv3_02/rv3_07 实证）**：模块根 `(_A or _B) and _C` 展平为 or 链、混合三元链重建保真差——B89 封闭判据（跳转目标排除）只覆盖操作数归属子型，分组识别判据本身（分组检测命中条件）对「内层 or + 外层 and」模块根形态不命中。锚点 `_build_grouped_boolop_expression` 分组检测段。建议 Round 3 登记新编号。
4. **【移交确认】**FIX_P3 §6 移交项全部复核属实：B87 残余（c04.CTryNest 发射位错位，读数持平）、B88 残余（x08.return_leaf 与 B78 纠缠）、B93（x05.with_in_match 镜像替换）、B94（x01.if_in_while NOP 假循环）、B97（x10.h_basic handler break——rv3_06 获又一实证）。另有在途 §6.6 观察项（预生成未登记 `_generated_regions`，依赖块级标记兜底）维持移交。
5. **【过程卫生】**：在途提交 3a9db846 引入 2 个杂散产物 `test_repros/round2/m01_docstring_orderOKOK.py`、`m08_module_stmtsOKOK.py`（pycdc 对 OK.py 再跑一次的双后缀误名），建议随整改提交删除。
6. **【报告口径】**：FIX_P3「新增方法 0（全部为既有方法内守卫/判据收窄）」仅对其自身基线（3a9db846 起）成立，批次整体（87e59c49 起）有 9 个新方法/新类；建议后续 FIX 报告声明基线时显式标注 commit 范围，避免复核歧义。
7. **【正面确认】**：本批复核未发现任何读数虚报；42 探针 +3 单元的终态（m12 3/3、x04 6/7、合计 172/196）与全部移交归因逐项独立复现成立；站桩 45/45 逐位持平；字节影响面干净；BOM/插桩/落地标记全过。

---

## 附：复核产物

- 本报告：`rounds/round2/REVIEW2.md`
- 变体探针：`test_repros/round2/rv3_01..rv3_07`（.py/.pyc/OK.py，未跟踪文件）
- 复核过程零 git 提交、跟踪文件零修改；基线复跑临时环境（/tmp/rv3_base）已清理。
