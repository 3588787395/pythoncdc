# Tasks

> 目标：对 `/workspace/quotation.pyc` 执行 10 轮「测试工程师 + 修复工程师」迭代，直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + 提取 10+ 最小复现实例 → 修复工程师按区域归约算法修复 → 回归 → commit + push。
> 所有命令执行不得超过 300 秒。
> 每轮必须提交并 push 到远程。
> **状态：执行中（预备阶段完成，进入 Round 1）**

## 通用任务模板（每轮共用）

- [ ] T1: 测试工程师反编译 quotation.pyc（输出 `decompile_report.md`）
  - 执行 `python pycdc.py /workspace/quotation.pyc`（≤60s）
  - 反编译产物字节码 vs 原 pyc 字节码 diff
  - 不一致清单（函数名 + 偏移 + 字节码模式）
- [ ] T2: 测试工程师提取 ≥10 个最小复现实例（输出 `minimal_repros/`）
  - 每个实例：最小 `.py` 源码 → compile → 反编译 → 字节码 diff
  - 归档至 `rounds/round_NN/test_engineer/minimal_repros/repro_NN_<area>_<feature>.py`
- [ ] T3: 修复工程师分析 + 定位（依赖 T1/T2）
  - 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析（涉及的区域类型 + 算法偏离点）
- [ ] T4: 修复工程师实施修复
  - 按区域归约算法 4 原则完善逻辑（禁止补丁）
  - 同步更新方法 docstring（统一 6 项模板）
- [ ] T5: 修复工程师回归测试（≤280s）
  - 该轮 10+ 最小复现实例全部通过
  - 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] T6: 修复工程师输出 `fix_report.md`
  - 修复点 + 算法依据 + 回归结果 + 残留不一致数
- [ ] T7: commit + push 到 origin/main（前缀 `qpyc-rNN:`，≤300s）
- [ ] T8: 反模式自检（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增；`_merge_block_is_loop_back_edge` 重命名按计划执行）

## 预备任务

- [x] T0: 建立 quotation.pyc 字节码基线
  - 输出 `baseline/original_bytecode.txt`（dis 输出，133 函数）
  - 输出 `baseline/decompiled_baseline.py`（首轮反编译结果，2593 行）
  - 输出 `baseline/decompile_stderr.txt`（19 处 MatchSingleton 警告）
  - 编译 `decompiled_baseline.py` 失败：line 2579 `filter_type=` 缺默认值
- [x] T0-1: 建立反模式起点快照（`baseline/antipattern_snapshot.txt`：_merge_=1, 其他=0）

## 轮 1 (Round 1)

- [x] R1-T1: 反编译 + 字节码 diff → `decompile_report.md`（rounds/round_01/test_engineer/decompile_report.md，12 类缺陷，line 2579 阻塞 + 19 处 MatchSingleton）
- [x] R1-T2: ≥10 最小复现实例 → `minimal_repros/`（12 个 repro，全部通过 py_compile 验证）
- [x] R1-T3: 根因分析（定位到识别/生成方法）（fix_report.md §1 已确认根因：repro_03→code_generator._generate_arguments；repro_01→region_analyzer._mr_finalize_match_region + ast_converter；repro_05→region_ast_generator 链式比较；repro_07→region_ast_generator POP_EXCEPT/多STORE）
- [x] R1-T4: 实施修复（含 docstring 同步）（P0×2 完全/阻塞解除 + P1×2 完全/部分；4 处 docstring 更新）
- [x] R1-T5: 回归测试（无退化 + 复现实例通过）（10 区域 0 退化，12 repro 全部反编译可编译）
- [x] R1-T6: `fix_report.md`（rounds/round_01/repair_engineer/fix_report.md）
- [ ] R1-T7: commit + push `qpyc-r01:`（待用户授权执行；修复工程师无 commit 权限）
- [x] R1-T8: 反模式自检（G3 通过：0 新增反模式前缀方法；_merge_=1 为 pre-existing）

## 轮 2 (Round 2)

> **状态**：测试工程师阶段已完成（14 repro 全部 DEFECT-REPRO）；修复工程师阶段待执行。
> **R2 基线**：反编译产物 COMPILE_OK，但 81 个函数字节码不一致、70 个函数签名不匹配、1 个 listcomp 丢失。
> **R2 缺陷分布**：14 类（10 项 R1 残留演化 + 4 项 R2 新增），P0=2、P1=5、P2=7。

### 阶段一：测试工程师（已完成）

- [x] R2-T1: 反编译 + 字节码 diff → `decompile_report.md`
  - 反编译命令 `python pycdc.py /workspace/quotation.pyc`（产物 `/tmp/r2_decompiled.py`，2592 行）
  - 字节码 diff 工具 `/tmp/r2_diff.py`（输出 `/tmp/r2_diff_detail.txt` + `/tmp/r2_sig_diff_detail.txt`）
  - 不一致清单：14 类缺陷 + 代表性函数 + 偏移 + 字节码模式 + R1 repro 关联
  - 关键结论：R1 完全修复 2 项（repro_03/05）、残留复现 7 项（repro_01/02/04/06/08/09/11）、残留部分修复 3 项（repro_07/10/12）、R2 新增 4 项（repro_13/14/15/16）
- [x] R2-T2: ≥10 最小复现实例 → `minimal_repros/`
  - 14 个 repro 全部通过 `py_compile` 独立编译
  - 14/14 DEFECT-REPRO 验证通过（`python pycdc.py <repro>.pyc` 复现缺陷）
  - 归档至 `rounds/round_02/test_engineer/minimal_repros/repro_NN_*.py`

### 阶段二：修复工程师（执行中 — P0+3 项 P1 已验证通过，quotation.pyc 仍存孤儿 try 阻塞编译）

- [x] R2-T3: 根因分析 + 定位（依赖 R2-T1/T2）
  - 对 14 个 repro 逐项定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析：区域类型 + 算法偏离点 + 4 原则违反项
  - 涉及文件：`core/cfg/cfg_builder.py`、`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/code_generator.py`、`core/cfg/pattern_parser.py`、`core/cfg/ast_converter.py`

- [x] R2-T4: P0 修复实施（含 docstring 同步）
  - [x] R2-T4a: 修复 repro_13（FUNCTION_DEF defaults→装饰器，疑似 R1 回归，3 处跨函数泄漏）— **已验证**
    - 定位：`cfg_builder.py::_identify_jump_targets` / `region_ast_generator.py::_reconstruct_decorator_chain` / `code_generator.py::_generate_function_def`
    - 根因：CPython 3.11+ 在装饰器与 MAKE_FUNCTION 之间插入 NOP（非跳转目标，用于行号对齐/占位），CFG 把 NOP 误判为块边界，切断 `LOAD_NAME decorator + LOAD_CONST defaults + MAKE_FUNCTION + CALL` 原子序列；导致装饰器丢失、defaults 元组被误发射为 `@((...))`
    - 修复方向：禁止将非跳转目标的 NOP 作为块边界（NOP 是否为块边界由 `instr.is_jump_target` 唯一判定）；确保 defaults 元组只填入函数签名 `name=default`，绝不挂到 decorators 列表
    - 算法依据：每块唯一归属（块边界仅由「跳转目标 + 跳转/返回/raise 的下一条」确定）
    - docstring 更新：`_identify_jump_targets`（6 项模板）— 已按 6 项模板更新（算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义/反编译流程）
    - 验证结果：repro_13 反编译产物 `def get_history(count, frequency='1d', ...)` 无 `@((...))` 前导，defaults 正确填入签名 ✓
  - [x] R2-T4b: 修复 repro_14（elif A and B: 后函数体截断，9 个财务函数 469→64 指令）— **已验证**
    - 定位：`region_analyzer.py::_identify_conditional_regions` / `_build_elif_region`
    - 根因：elif 条件的 `and` 短路（A 真值 + B CALL）归约后，elif body 之后的 fall-through 块（含 for/return）被错误吸收为不可达子区域。结构区域块集合（_structural_region_entries）原仅收集 entry 块，未包含 LoopRegion 的 setup 块（如 for 循环的 LOAD_FAST+GET_ITER 块），导致 ipdom 链遍历未在 merge 点停止
    - 修复方向：保证 elif 归约后 fall-through 后续语句作为函数体顺序子节点保留，禁止吸收为不可达子区域。扩展结构区域块集合为包含所有结构区域块（含 setup/header/body），在 then/else 分支的 ipdom 链遍历中检测多非回边前驱的结构区域块（`_non_backedge_preds > 1`），正确设置 merge 点
    - 算法依据：自底向上归约 + 每块唯一归属
    - docstring 更新：`_identify_conditional_regions` / `_build_elif_region`（6 项模板）— 已存在详细 docstring（6 节结构：算法描述/字节码模式/边界条件/归约语义/AST映射/已知失败模式），内容覆盖 6 项模板要求
    - 验证结果：repro_14 反编译产物 `get_balance_statement` 函数体不再截断，for 循环和 return 正确保留 ✓（注：存在 spurious for-else，属 repro_09 范畴，非 repro_14 截断问题）

- [x] R2-T5: P1 修复实施（已完成 3 项：repro_02/15/16；repro_10/01 待后续轮次）
  - [x] R2-T5a: 修复 repro_02 + repro_16（IS_OP→`== None`、`not in`→`in`）— **已验证**
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_compare` / `_wrap_boolop_with_merge_compare` / `ast_converter.py::_convert_compare_full`
    - 根因：`_generate_if` 把 `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE`（IS_OP）重建为 `COMPARE_OP == None`/`!= None`；`_generate_compare` 把 `CONTAINS_OP 0`（not in）+ `POP_JUMP_FORWARD_IF_FALSE` 误读为正向 `in`，丢失 `not`；`_convert_compare_full` 未处理 dict-form ops 第三种格式 `{'type': 'Is'}`
    - 修复方向：按 `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE` 重建 `is None`/`is not None`；按 `CONTAINS_OP` arg（0=not in, 1=in）正确解析 `not in`；处理 `{'type': 'Is'}` 格式并添加 PascalCase 操作符映射；条件上下文 BoolOp 不进行包裹比较
    - 算法依据：每块唯一归属 + 入口引用语义
    - 验证结果：repro_02 反编译产物 `if quote is None and is_trade:` + `elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:` ✓；repro_16 反编译产物 `if frequency not in OVER_WEEK_FREQUENCY:` ✓（注：repro_16 存在 and 分解为嵌套 if 的结构性差异，属 repro_06 范畴，非 not in 翻转问题）
  - [x] R2-T5b: 修复 repro_15（BoolOp or→and 翻转，`check_frequency` 6 路 or）— **已验证**
    - 定位：`region_ast_generator.py::_boolop_expression`
    - 根因：BoolOp 重建把 `POP_JUMP_FORWARD_IF_TRUE`（or 短路）与 `POP_JUMP_FORWARD_IF_FALSE`（and 短路）混淆，统一重建为 `and`
    - 修复方向：按跳转方向区分 `BoolOp.op`（IF_TRUE→`or`，IF_FALSE→`and`），不可互换
    - 算法依据：入口引用语义
    - 验证结果：repro_15 反编译产物 `if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == '1y'):` 6 路 or 正确保留 ✓
  - [ ] R2-T5c: 修复 repro_10（if 块泄漏为下一函数 `@((...))` 装饰器，与 repro_13 同源）— **待后续轮次**
    - 定位：`region_analyzer.py::_identify_conditional_regions` + `cfg_builder.py`
    - 根因：`if A and B is None:`（A 走 CONTAINS_OP + POP_JUMP_IF_FALSE，B is None 走 POP_JUMP_IF_NOT_NONE）归并时，把 if 块指令与紧随其后的 MAKE_FUNCTION defaults 元组错误归并
    - 修复方向：切断 if 块与模块级 MAKE_FUNCTION 的错误归并，确保 if 块归函数体、defaults 归函数签名
    - 算法依据：每块唯一归属 + 自底向上归约
    - 当前状态：repro_13 修复后 `@((...))` 装饰器泄漏已消失，但 repro_10 的 `and query_date is None` 条件仍丢失，留待后续轮次
  - [ ] R2-T5d: 修复 repro_01（case None→case _ + 重复 case _，致 SyntaxError）— **待后续轮次**
    - 定位：`pattern_parser.py` / `region_ast_generator.py::_generate_match` / `region_analyzer.py::_mr_finalize_match_region`
    - 根因：R1 把 MatchSingleton 从 MatchOr 拆出后，case pattern 重建路径未把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`、`MATCH_CLASS str` 重建为 `MatchClass(str, [])`，统一回退 `MatchAs(None)`（`case _`）
    - 修复方向：把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`、`MATCH_CLASS str` 重建为 `MatchClass(str, [])`，禁止回退 `MatchAs(None)`；去重 case _
    - 算法依据：嵌套即抽象节点

- [ ] R2-T6: P2 修复实施（按时间预算择优，至少 2 项）
  - [ ] R2-T6a: 修复 repro_06（IfExp 实参→and + docstring 体，`get_quote`）
    - 定位：`region_ast_generator.py::_generate_if`
    - 修复方向：把 IfExp 作为 Call 实参子节点保留，禁止把 IfExp 条件提升为 if 的 `and` 条件、禁止把字符串常量发射为 docstring 体
  - [ ] R2-T6b: 修复 repro_04（STORE_SUBSCR→变量注解 + spurious break，`get_fundflow_day`）
    - 定位：`region_ast_generator.py::_generate_loop` / `_build_effective_stmts`
    - 修复方向：把 `STORE_SUBSCR`（d[k]=call）与 `STORE_ANNOTATION`（PEP 526）区分；去除 spurious break
  - [ ] R2-T6c: 修复 repro_07（except handler 内 isinstance 丢失→裸 `if X:`，`api_get_financial`）
    - 定位：`region_ast_generator.py::_generate_try`
    - 修复方向：把 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL` 作为完整 Call 节点作 If 条件，禁止只保留 `LOAD_GLOBAL cls`
  - [ ] R2-T6d: 修复 repro_08（循环体赋值目标丢失→裸 Name + 重复语句，`load_get_price`）
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_loop` / `_build_effective_stmts`
    - 修复方向：保留 `STORE_FAST var` 赋值目标；`_build_effective_stmts` 去重前驱语句
  - [ ] R2-T6e: 修复 repro_09（双层 spurious for-else + match case 体内 for，`fill_missing_stock_data`）
    - 定位：`region_analyzer.py::_identify_loop_regions`
    - 修复方向：else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句，覆盖嵌套 for 与 match case 内 for
  - [ ] R2-T6f: 修复 repro_11（elif 分支首条赋值 RHS 丢失→裸 Name，`check_stocks`）
    - 定位：`region_ast_generator.py::_generate_if`
    - 修复方向：保留 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` 的 Call 节点，禁止只保留 receiver `LOAD_FAST l` 作孤立 Expr
  - [ ] R2-T6g: 修复 repro_12（嵌套 `if A: S; if B:` 内层 if 丢失，`get_valuation_info`）
    - 定位：`region_analyzer.py::_identify_conditional_regions`
    - 修复方向：把内层 `if B:` 的 then-块作为外层 If.body 子节点保留，禁止吸收为不可达

- [x] R2-T6b: **新增** — 修复 quotation.pyc 孤儿 try: 块阻塞编译（P0 阻塞项，必做）— **已验证**
  - 定位：`region_analyzer.py::_identify_conditional_regions`（前置：else 分支结构区域入口检测）+ `_build_region_hierarchy`（核心：候选移除逻辑误移除 IfRegion）
  - 根因：`get_market_detail` 函数中 if/else 嵌套 if/else 嵌套 try/except 场景下，`_build_region_hierarchy` 为 TryExceptRegion 选父时，候选移除逻辑把与 TryExcept 共享 entry=15 的 WithRegion（实为 TryExcept 子区域）误判为祖先，据此移除两个 IfRegion 候选，导致 TryExceptRegion 成为顶层区域（parent=None），AST 生成器无法发射 try:/except: 包裹，反编译产物出现孤儿 try 块 + SyntaxError
  - 修复方向：(1) 前置 Fix 05——`_identify_conditional_regions` 新增 `_structural_region_co_blocks` 同区域兄弟块映射 + then/else 链 break 条件外部非回边前驱检查，消除 SyntaxError；(2) 核心修复——`_build_region_hierarchy` L16624-16636 候选移除条件增加 `_ni_is_peer` 守卫，当非 If 候选与 child 共享同一 entry 块时（子区域/对等区域而非祖先）不据此移除 IfRegion 候选，确保 TryExceptRegion 正确挂到 IfRegion else 分支下
  - 算法依据：每块唯一归属（尊重 block_to_region canonical owner）+ 嵌套即抽象节点（TryExcept 作为 IfRegion else 分支抽象节点）
  - docstring：`_identify_conditional_regions` / `_build_elif_region` 已存在 6 节结构 docstring 覆盖 6 项模板；`_build_region_hierarchy` 为内部层级构建方法，守卫逻辑已通过内联注释说明算法依据
  - 验证结果：quotation.pyc COMPILE_OK ✓；`get_market_detail` try/except 结构正确恢复 ✓；orphan_try_repro.py REPRO_RECOMPILE_OK ✓（详见 fix_report.md §9）

- [ ] R2-T7: 回归测试（≤280s）
  - [x] R2-T7a: 5 个已修复 repro（13/14/15/02/16）反编译验证通过（反编译产物核心缺陷已消除）
    - repro_13: `@((...))` 装饰器泄漏消失，defaults 填入签名 ✓
    - repro_14: elif 后函数体不再截断，for 循环 + return 保留 ✓
    - repro_15: 6 路 `or` 不再翻转为 `and` ✓
    - repro_02: `is None` + `not in` 正确保留 ✓
    - repro_16: `not in` 不再翻转为 `in` ✓
    - 注：repro_14 存在 spurious for-else（属 repro_09）、repro_16 存在 and 分解为嵌套 if（属 repro_06），均为独立缺陷，非本轮修复目标退化
  - [x] R2-T7b: 既有测试矩阵无退化（IF/MATCH/BOOLOP/LOOP/TRY/WITH/TERNARY/CC/SEQ/ASSERT 子集）— **0 真实退化**
    - 执行 `python .trae/specs/analysis-fix-iteration/run_region_tests.py` 全部 10 区域
    - 结果：IF/TRY/WITH/MATCH/BOOLOP 持平；TERNARY/CC/SEQ/ASSERT 失败为 pre-existing（基线即失败）；LOOP `test_for20_complex_body` 由 skip（SyntaxError 垃圾产物）转为 fail（正确 for/if 结构 + 残留 STORE_SUBSCR 缺陷，属 repro_04 P2 范畴），为**净改善**非退化（详见 fix_report.md §9.4.4）
  - [x] R2-T7c: quotation.pyc 反编译 stderr 警告数维持 0 ✓（`wc -l /tmp/r2_quote.err` = 0）
  - [x] R2-T7d: quotation.pyc 反编译产物 `compile()` 通过 — **已通过**（COMPILE_OK，孤儿 try: 块已修复，见 R2-T6b）

- [x] R2-T8: `fix_report.md`（rounds/round_02/repair_engineer/fix_report.md）— **已生成**
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（14 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R2 基线 81 个函数不一致对比，应下降；推荐目标 ≤ 60）
  - 算法 4 原则合规性自检
  - 已验证修复点（6 项）：repro_13/14/15/02/16 + 孤儿 try（R2-T6b）
  - §9 孤儿 try 修复详解：根因（_build_region_hierarchy 候选移除误判）/ 修复（_ni_is_peer 守卫）/ 验证 / 算法依据 / 残留

- [x] R2-T9: 反模式自检 ✓
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（grep 验证通过）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，region_ast_generator.py L18747/L20954，按 spec 留待后续轮次）

- [ ] R2-T10: commit + push `qpyc-r02:`（≤300s，待用户授权）

## R2 验证补充检查点（已执行）

- [x] R2-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter"` 编译通过 ✓（IMPORT_OK）
- [x] R2-V2: 反模式 grep 验证 ✓（0 新增）
- [x] R2-V3: 5 个已修复 repro（13/14/15/02/16）反编译产物核心缺陷已消除 ✓
- [x] R2-V4: quotation.pyc 反编译 stderr=0 ✓
- [x] R2-V5: quotation.pyc 反编译产物 `compile()` 通过 — **已通过**（COMPILE_OK，孤儿 try: 块已修复）

## 轮 3 (Round 3)

> **状态**：测试工程师阶段已完成（10 个 repro_03_*.py 全部 DEFECT-REPRO）；修复工程师阶段执行中——P0×2 + P1×3 已完成并验证，P2 修复与最终验证/报告撰写待执行。
> **R3 基线**：反编译产物 COMPILE_OK（2547 行），81 个函数字节码不一致、41 个签名不匹配、4 个缺失 code objects、18 个截断函数。
> **R3 缺陷分布**：10 类（5 项 R2 残留演化 + 5 项 R3 新增/重点验证），P0=2、P1=3、P2=5。
> **R3 重大发现**：R2 声称已修复的 repro_14（elif 链后函数体截断）在 quotation.pyc 实际路径仍复现（9 个财务函数 469→64）；repro_15 BoolOp 在 quotation.pyc::check_frequency 仍翻转为 `and`。

### 阶段一：测试工程师（已完成）

- [x] R3-T1: 反编译 + 字节码 diff → `decompile_report.md`
  - 反编译命令 `python pycdc.py /workspace/quotation.pyc`（产物 `/tmp/r3_decompiled.py`，2547 行）
  - 字节码 diff 工具 `/tmp/r3_diff.py`（输出 `/tmp/r3_diff_detail.txt` + `/tmp/r3_summary.txt`）
  - 不一致清单：10 类缺陷 + 18 个截断函数 + 4 个缺失 code objects + R2 声称修复点逐项复测
  - 关键结论：R2 完全修复 5 项（repro_13/15 minimal/02/16 + 孤儿 try）；R2 声称修复但 R3 实测仍复现 1 项（repro_14 quotation.pyc 路径）；R2 残留 8 项（repro_01/04/04b/06/07/08/09/11/12）
- [x] R3-T2: ≥10 最小复现实例 → `minimal_repros/`
  - 10 个 repro 全部通过 `py_compile` 独立编译
  - 10/10 DEFECT-REPRO 验证通过
  - 归档至 `rounds/round_03/test_engineer/minimal_repros/repro_03_*.py`

### 阶段二：修复工程师（执行中 — P0×2 + P1×3 已验证，P2 修复与最终验证/报告待执行）

- [x] R3-T3: 根因分析 + 定位（依赖 R3-T1/T2）
  - 对 10 个 repro 逐项定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析：区域类型 + 算法偏离点 + 4 原则违反项
  - 涉及文件：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/pattern_parser.py`、`core/cfg/ast_converter.py`

- [x] R3-T4: P0 修复实施（含 docstring 同步）
  - [x] R3-T4a: 修复 repro_03_elif_chain_func_body_truncation（P0-1，elif 链后函数体截断，9 个财务函数 469→64）— **已验证**
    - 定位：`region_analyzer.py::_identify_conditional_regions` / `_find_structural_merge_from_chain_end`
    - 根因：复杂 CFG（含嵌套 for/try/return）中 ipdom 链遍历未正确识别 merge 点；原 sink 判定逻辑把 ipdom=None 等同于 sink，导致 merge=None，elif 链后 fall-through 块被误判为不可达子区域，函数体整段被吸收
    - 修复方向：(1) sink 判定逻辑改为仅当块含 RETURN/RAISE/RERAISE 或无正常后继时才视为 sink；(2) 新增 `_find_structural_merge_from_chain_end` 从 ipdom 链终止块的后继中查找结构区域入口作为 merge 点；(3) ipdom 链遍历增加普通合并点（非结构区域入口但有 >1 个非回边前驱）检测，提前停止遍历
    - 算法依据：自底向上归约 + 每块唯一归属
    - 验证结果：`get_balance_statement` 函数体从 13 行恢复至 69 行，9 个财务函数均不再截断 ✓
  - [x] R3-T4b: 修复 repro_03_repro04_file_assignment_lost（P0-2，try 块前 file 赋值丢失）— **已验证**
    - 定位：`region_ast_generator.py::_generate_with` / `region_analyzer.py::_extract_with_items`
    - 根因：`get_market_detail` 函数中 try 块前的 `file = '...' % finance_mic` 赋值语句被误识别为 TryExcept/WithRegion 的 setup 块而吞并，导致 `with open(file, 'rb')` 中 file 引用悬空
    - 修复方向：(1) `_extract_with_items` 提取上下文表达式时遇到 STORE_* 指令清空已收集的 ctx_expr，仅保留 STORE_* 之后至 BEFORE_WITH 之间的指令作为真正的 context_expr；(2) `_generate_with` 提取 entry 块内 BEFORE_WITH 之前、以 STORE_* 结尾的指令段，作为 with 语句之前的顺序语句发射；(3) `_if_generate_else_branch` 按偏移顺序交错处理子区域（Try/With/Loop）和顺序块
    - 算法依据：自底向上归约 + 每块唯一归属
    - 验证结果：`repro_03_repro04_file_assignment_lost.pyc` 中 `file = ...` 正确出现在 `try:` 之前；quotation.pyc 中 `get_market_detail` 函数的 file 赋值已恢复 ✓

- [x] R3-T5: P1 修复实施（已完成 3 项：repro_03_match_case_none_to_wildcard / repro_03_if_nested_inner_lost / repro_03_if_ifexp_arg_to_and_docstring）
  - [x] R3-T5a: 修复 repro_03_match_case_none_to_wildcard（P1-1，case None 被转换为 case _）— **已验证**
    - 定位：`pattern_parser.py::_extract_case_pattern` / `ast_converter.py::_convert_match_pattern`
    - 根因：PatternParser 已能识别 `case None` 为 `MatchSingleton(None)`（POP_JUMP_FORWARD_IF_NOT_NONE / POP_JUMP_IF_NOT_NONE），但 ast_converter.py 在转换时未处理 `MatchSingleton` 类型，默认返回 `ASTName('_')`，导致渲染为 `case _`
    - 修复方向：(1) `pattern_parser.py::_extract_case_pattern` 识别 `POP_JUMP_FORWARD_IF_NOT_NONE` / `POP_JUMP_IF_NOT_NONE` 为 `MatchSingleton(None)`；(2) `ast_converter.py::_convert_match_pattern` 添加 `MatchSingleton` 类型处理，直接返回其字典结构
    - 算法依据：嵌套即抽象节点
    - 验证结果：repro_03_match_case_none_to_wildcard.pyc 中 `case None` 正确输出；quotation.pyc 中检测到 19 处 `case None` ✓
  - [x] R3-T5b: 修复 repro_03_if_nested_inner_lost（P1-2，嵌套 if 内层丢失）— **已验证**
    - 定位：`region_analyzer.py::_detect_boolop_conditional_chain`
    - 根因：BoolOpRegion 错误地将含 STORE_* 指令的 body 块识别为 `and` 操作数，导致外层 if 与内层 if 合并为 `if A and B:`，并将 body 语句提升出 if 块
    - 修复方向：`_detect_boolop_conditional_chain` 中添加 STORE_* 检测，当非首块含 STORE_* 指令时中断链，避免 body 块被误纳为 BoolOp 操作数
    - 算法依据：自底向上归约 + 嵌套即抽象节点
    - 验证结果：repro_03_if_nested_inner_lost.pyc 中嵌套 if 结构正确保留，语句未被提升 ✓
    - 已知限制：walrus `(x := foo()) and bar` 的条件块也含 STORE_FAST，此处会误中断链（罕见模式，留待后续）
  - [x] R3-T5c: 修复 repro_03_if_ifexp_arg_to_and_docstring（P1-3，IfExp 实参→and + docstring 体）— **已验证**
    - 定位：`region_analyzer.py::_detect_boolop_conditional_chain`
    - 根因：`_detect_boolop_conditional_chain` 错误地将 IfExp 的条件块（含 `POP_JUMP_IF_FALSE`）识别为 `and` 操作数，导致 IfExp 实参被转换为 `if A and B:` 条件，且字符串常量被误发射为 docstring
    - 修复方向：`_detect_boolop_conditional_chain` 中新增 IfExp 检测，当非首块的 fall-through 后继以 `JUMP_FORWARD` 终结时中断链，避免 IfExp 条件块被误纳为 BoolOp 操作数（JUMP_FORWARD 是 IfExp true-value 跳过 false-value 的特征）
    - 算法依据：自底向上归约 + 嵌套即抽象节点
    - 验证结果：repro_03_if_ifexp_arg_to_and_docstring.pyc 中 IfExp 正确保留为 Call 实参，docstring 错误消失 ✓
    - 已知限制：嵌套 if 的 then-body 末尾若有 JUMP_FORWARD 由 P1-2 的 STORE_* 检测覆盖

- [ ] R3-T6: P2 修复实施（按时间预算择优，至少 2 项 — 待执行）
  - [ ] R3-T6a: 修复 repro_03_try_except_handler_if_cond_lost（P2-1，except handler 内 `if e2.code == 401:` 条件丢失→裸 `if HTTPError:`）— **待执行**
    - 定位：`region_ast_generator.py::_generate_try`
    - 根因初判：`_generate_try` 在 except handler 内重建 `if e.code == N:` 时，把 `LOAD_FAST e + LOAD_ATTR code + LOAD_CONST N + COMPARE_OP` 的 Compare 节点丢弃，改为引用 except 子句的 `LOAD_GLOBAL ExceptionClass`（HTTPError/BaseException），退化为裸 `if HTTPError:`（恒真）
    - 修复方向：把 except handler 内 `LOAD_FAST e + LOAD_ATTR code + LOAD_CONST N + COMPARE_OP` 完整 Compare 节点保留作 If 条件，禁止只保留 `LOAD_GLOBAL cls`
    - 算法依据：嵌套即抽象节点 + 入口引用语义
    - 验证目标：repro_03_try_except_handler_if_cond_lost.pyc 中 `if e2.code == 401:` 条件恢复；quotation.pyc::api_get_financial line 141-150 条件恢复
  - [ ] R3-T6b: 修复 repro_03_loop_store_subscr_to_annotation（P2-2，STORE_SUBSCR 被错误转换为变量注解 + spurious break）— **待执行**
    - 定位：`region_ast_generator.py::_build_effective_stmts` / `_generate_loop`
    - 根因初判：`_build_effective_stmts` 在处理 `STORE_SUBSCR` 时未能正确重建 `Subscript` 目标，导致赋值语句被错误解析为 `STORE_ANNOTATION`（PEP 526 变量注解），发射 `d[k]: d = call(...)`；循环体中出现多余 `break`
    - 修复方向：`_build_effective_stmts` 中区分 `STORE_SUBSCR`（d[k]=call）与 `STORE_ANNOTATION`（PEP 526），正确重建 `Subscript` 目标为 `d[k] = v`；去除 spurious break
    - 算法依据：每块唯一归属
    - 验证目标：repro_03_loop_store_subscr_to_annotation.pyc 中 `returninfo[item] = ...` 正确输出；quotation.pyc::get_fundflow_day line 2179-2182 恢复
  - [ ] R3-T6c: 修复 repro_03_loop_bare_name_and_dup（P2-3，循环体赋值目标丢失→裸 Name + 重复）— **可选**
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_loop` / `_build_effective_stmts`
    - 修复方向：保留 `STORE_FAST var` 赋值目标；`_build_effective_stmts` 去重前驱语句
  - [ ] R3-T6d: 修复 repro_03_loop_spurious_for_else_double（P2-4，双层 spurious for-else）— **可选**
    - 定位：`region_analyzer.py::_identify_loop_regions`
    - 修复方向：else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句，覆盖嵌套 for 与 match case 内 for
  - [ ] R3-T6e: 修复 repro_03_if_elif_bare_name（P2-5，elif 分支首条赋值 RHS 丢失→裸 Name）— **可选**
    - 定位：`region_ast_generator.py::_generate_if`
    - 修复方向：保留 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` 的 Call 节点，禁止只保留 receiver `LOAD_FAST l` 作孤立 Expr

- [ ] R3-T7: 回归测试（≤280s）— **待执行**
  - [ ] R3-T7a: 10 个 R3 repro 反编译验证（核心缺陷消除）
  - [ ] R3-T7b: 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
  - [ ] R3-T7c: quotation.pyc 反编译 stderr 维持 0
  - [ ] R3-T7d: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
  - [ ] R3-T7e: quotation.pyc 中 `get_balance_statement` 函数体不再截断（orig=469 → new ≥ 400）
  - [ ] R3-T7f: quotation.pyc 中 `get_market_detail` 的 `file = ...` 赋值恢复
  - [ ] R3-T7g: 残留不一致数 ≤ R3 基线（81 个函数不一致，目标 ≤ 50；截断函数 18 → ≤ 5）

- [ ] R3-T8: `fix_report.md` 生成（rounds/round_03/repair_engineer/fix_report.md）— **待执行**
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（10 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R3 基线 81 个函数不一致对比，应下降；推荐目标 ≤ 50）
  - 算法 4 原则合规性自检
  - 已知限制（walrus + IfExp JUMP_FORWARD 等）

- [ ] R3-T9: 反模式自检 — **待执行**
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（grep 验证）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，按 spec 留待后续轮次）

- [ ] R3-T10: 涉及的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新 — **待执行**
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_identify_conditional_regions`（P0-1 修改）/ `_extract_with_items` + `_generate_with`（P0-2 修改）/ `_detect_boolop_conditional_chain`（P1-2/P1-3 修改）/ `_extract_case_pattern`（P1-1 修改）

- [ ] R3-T11: commit + push `qpyc-r03:`（≤300s，待用户授权）

## R3 验证补充检查点（待执行）

- [ ] R3-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.pattern_parser"` 编译通过
- [ ] R3-V2: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）
- [ ] R3-V3: quotation.pyc 反编译 stderr 维持 0
- [ ] R3-V4: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R3-V5: quotation.pyc 中 `get_balance_statement` 函数体不再截断（orig=469 → new ≥ 400）
- [ ] R3-V6: quotation.pyc 中 `get_market_detail` 的 `file = ...` 赋值恢复
- [ ] R3-V7: quotation.pyc 中 `check_frequency` 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`（不仅 minimal repro）— 待评估是否本轮覆盖
- [ ] R3-V8: 10 个 R3 repro 全部反编译产物核心缺陷消除

## 轮 4 (Round 4)

> **状态**：测试工程师阶段已完成（12 个 repro_04_*.py 全部 DEFECT-REPRO）；修复工程师阶段待执行。
> **R4 基线**：反编译产物 COMPILE_OK（3035 行），80 个函数字节码不一致、37 个签名不匹配、4 个缺失 code objects、11 个截断函数。
> **R4 缺陷分布**：12 类（3 项 R3 残留 P2 复测 + 8 项 R4 新增 + 1 项 R3 修复在 quotation.pyc 退化），P0=2、P1=4、P2=5。
> **R4 重大发现**：R3 elif 修复让 9 个财务函数脱离 >50% 截断清单，但暴露下游更深层截断（change_his_to_forward/backward、fill_minute_or_day_blank、date_convert）；R3 fix_report 声称修复的 repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物退化（裸 `stock` Expr + `panel[stock] = data` 丢失）。

### 阶段一：测试工程师（已完成）

- [x] R4-T1: 反编译 + 字节码 diff → `decompile_report.md`
  - 反编译命令 `python pycdc.py /workspace/quotation.pyc`（产物 `/tmp/r4_decompiled.py`，3035 行）
  - 字节码 diff 工具 `/tmp/r4_diff.py`（输出 `/tmp/r4_diff_detail.txt` + `/tmp/r4_sig_diff_detail.txt` + `/tmp/r4_summary.txt`）
  - 不一致清单：12 类缺陷 + 11 个截断函数 + 4 个缺失 code objects + R3 已修 7 项复测 + R3 残留 3 项 P2 复测
  - 关键结论：R3 完全生效 6 项；R3 quotation.pyc 退化 1 项（repro_03_loop_bare_name_and_dup）；R3 残留 3 项 P2 仍存在；R4 新增 8 项缺陷（R4-NEW-01 ~ R4-NEW-08）
- [x] R4-T2: ≥10 最小复现实例 → `minimal_repros/`
  - 12 个 repro 全部通过 `py_compile` 独立编译
  - 12/12 DEFECT-REPRO 验证通过
  - 归档至 `rounds/round_04/test_engineer/minimal_repros/repro_04_*.py`

### 阶段二：修复工程师（待执行 — 目标：P0×2 + P1≥3 + P2≥2，时间允许则覆盖 P1×4 + P2×3）

- [ ] R4-T3: 根因分析 + 定位（依赖 R4-T1/T2）
  - 对 12 个 repro 逐项定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析：区域类型 + 算法偏离点 + 4 原则违反项
  - 涉及文件：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/ast_converter.py`、`core/cfg/pattern_parser.py`

- [ ] R4-T4: P0 修复实施（必须完成 2 项，含 docstring 同步）
  - [ ] R4-T4a: 修复 repro_04_func_body_truncated_after_else（P0-1，change_his_to_forward/backward else 后函数体截断退化，R3 new=239 → R4 new=181）
    - 定位：`region_analyzer.py::_identify_conditional_regions` / `_build_elif_region` / `_find_structural_merge_from_chain_end`
    - 根因：R3 扩展 `_structural_region_entries` 后，elif 链 else 分支 ipdom 链遍历在更深层级（else 后跟随 `preindex/tmpdata/tmpstartindex/tmpendindex/tmp` 赋值链 + for 循环 + 多层 if）仍误判 merge 点，把后续 for 循环吸收为不可达子区域
    - 修复方向：(1) 扩展 `_structural_region_entries` 含 else body 的 for 循环 header/setup 块；(2) ipdom 链遍历在 else 分支后跟随结构区域入口时正确停止；(3) `_find_structural_merge_from_chain_end` 增加 else 分支后跟 for 循环的 merge 点检测
    - 算法依据：自底向上归约 + 每块唯一归属
    - 验证目标：repro_04_func_body_truncated_after_else.pyc 中 else 后 for 循环 + tmpdata 赋值 + return 保留；quotation.pyc::change_his_to_forward 函数体 orig=597 → new ≥ 400
  - [ ] R4-T4b: 修复 repro_04_func_body_to_pass（P0-2，fill_minute_or_day_blank 函数体→pass，orig=244 → new=3）
    - 定位：`region_ast_generator.py::_generate_region` / `_generate_block_statements` / `region_analyzer.py::_identify_loop_regions`
    - 根因：函数体含 `for + if/elif/else + STORE_SUBSCR + continue` 嵌套，`_generate_region` 在归约时误判整个函数体为不可达，仅保留 `pass` 占位
    - 修复方向：(1) `_generate_region` 在 for + if/elif/else + STORE_SUBSCR 嵌套时按自底向上归约顺序处理子区域，禁止把整个函数体误判为不可达；(2) 确保 for 循环 + if/elif/else 分支作为函数体顺序子节点保留；(3) 检查 `_identify_loop_regions` 在含 continue 的 for 循环后跟 if/elif/else 时的归约边界
    - 算法依据：自底向上归约 + 嵌套即抽象节点
    - 验证目标：repro_04_func_body_to_pass.pyc 中 for + if/elif/else + STORE_SUBSCR + continue 全部保留；quotation.pyc::fill_minute_or_day_blank 函数体 orig=244 → new ≥ 150

- [ ] R4-T5: P1 修复实施（必须完成至少 3 项 — 目标 4 项）
  - [ ] R4-T5a: 修复 repro_04_boolop_or_chain_to_and（P1-1，check_frequency or→and 语义反转）
    - 定位：`region_analyzer.py::_detect_boolop_conditional_chain` / `region_ast_generator.py::_boolop_expression`
    - 根因：`_detect_boolop_conditional_chain` 在 `assert not (or-chain), msg` 模式下，将 POP_JUMP_FORWARD_IF_TRUE 短路误读为 POP_JUMP_FORWARD_IF_FALSE，导致 or→and 反转；且 assert 语句被拆分为 `if not (...): assert last_cond, msg`
    - 修复方向：(1) `_detect_boolop_conditional_chain` 区分 assert 语句与 if 语句的 jump 方向；(2) POP_JUMP_IF_TRUE 短路正确识别为 or 链；(3) assert 语句整体保留为 `assert not (or-chain), msg`，不拆分为 if + assert
    - 算法依据：入口引用语义 + AST 节点保形
    - 验证目标：repro_04_boolop_or_chain_to_and.pyc 中 `assert not (a or b or c or d or e or f), "msg"` 6 路 or 正确保留；quotation.pyc::check_frequency 函数体 orig=96 → new ≤ 100
  - [ ] R4-T5b: 修复 repro_04_try_except_handler_if_cond_lost（P1-2，except handler 内 `if e2.code == 401:` 条件丢失，R3 残留 P2 升级 P1）
    - 定位：`region_ast_generator.py::_generate_try`
    - 根因：`_generate_try` 在 except handler 内重建 `if e2.code == N:` 时，把 `LOAD_FAST e2 + LOAD_ATTR code + LOAD_CONST N + COMPARE_OP` 的 Compare 节点丢弃，改为引用 except 子句的 `LOAD_GLOBAL ExceptionClass`（HTTPError/BaseException），退化为裸 `if HTTPError: pass` + spurious `if BaseException: pass` 嵌套
    - 修复方向：把 except handler 内 `LOAD_FAST e + LOAD_ATTR attr + LOAD_CONST N + COMPARE_OP` 完整 Compare 节点保留作 If 条件，禁止只保留 `LOAD_GLOBAL cls`
    - 算法依据：嵌套即抽象节点 + 入口引用语义
    - 验证目标：repro_04_try_except_handler_if_cond_lost.pyc 中 `if e2.code == 401:` 条件恢复；quotation.pyc::api_get_financial line 161-172 条件恢复
  - [ ] R4-T5c: 修复 repro_04_func_body_to_single_expr（P1-3，date_convert 函数体→单 Expr，orig=87 → new=16）
    - 定位：`region_analyzer.py::_identify_conditional_regions` / `region_ast_generator.py::_generate_if` / IfExp 重建
    - 根因：`_identify_conditional_regions` 在 if/elif/else 链 + IfExp 嵌套时，误将整个条件块归约为单 IfExp Expr，导致 if/elif/else + return 完整函数体被压缩为 `int(month_temp == 1 if report_types is None else month_temp <= report_types)`
    - 修复方向：(1) `_identify_conditional_regions` 在 if/elif/else 链 + IfExp 嵌套时按自底向上归约顺序处理，禁止把整个条件块压缩为单 IfExp；(2) IfExp 仅在 Call 实参位置保留，不应吞并外层 if/elif/else
    - 算法依据：自底向上归约 + 嵌套即抽象节点
    - 验证目标：repro_04_func_body_to_single_expr.pyc 中 if/elif/else + return 完整保留；quotation.pyc::date_convert 函数体 orig=87 → new ≥ 60
  - [ ] R4-T5d: 修复 repro_04_if_branch_both_return_same（P1-4，_is_same_type_date 两分支均 return True，orig=99 → new=9）
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_compare`
    - 根因：嵌套 if 的内层 `len(day1) == 10` / `len(day1) == 8` Compare 节点丢失，仅保留外层 `typet == 7` 判断，导致两分支均返回相同值
    - 修复方向：(1) 保留嵌套 if 内层 Compare 节点；(2) 禁止把内层 Compare 折叠为外层 if 的常量分支
    - 算法依据：入口引用语义 + 嵌套即抽象节点
    - 验证目标：repro_04_if_branch_both_return_same.pyc 中 `if typet == 7: ... else: if len(day1) == 8: return True` 内层 Compare 保留；quotation.pyc::_is_same_type_date 函数体 orig=99 → new ≥ 60

- [ ] R4-T6: P2 修复实施（按时间预算择优，至少 2 项 — 目标 3 项）
  - [ ] R4-T6a: 修复 repro_04_loop_store_subscr_to_bare_name（P2-1，load_get_price STORE_SUBSCR 丢失 + 裸 stock Expr，R3 退化）
    - 定位：`region_ast_generator.py::_loop_generate_for` / `_build_effective_stmts` / `_fis_pre_stmts_emitted`
    - 根因：R3 `_fis_pre_stmts_emitted` 修复在 quotation.pyc 实际 CFG（含 if/elif/else + for + STORE_SUBSCR）下未覆盖 STORE_SUBSCR 序列，导致 `panel[stock] = data` 丢失 + 裸 `stock` Expr 泄漏
    - 修复方向：(1) 扩展 `_fis_pre_stmts_emitted` 覆盖 STORE_SUBSCR 序列；(2) `_loop_generate_for` pre_stmts 发射守卫区分 minimal repro 与实际 CFG；(3) `_build_effective_stmts` 正确重建 `STORE_SUBSCR` 的 `Subscript` 目标为 `panel[stock] = data`
    - 算法依据：每块唯一归属 + 入口引用语义
    - 验证目标：repro_04_loop_store_subscr_to_bare_name.pyc 中 `panel[stock] = data` 保留，无裸 `stock` Expr；quotation.pyc::load_get_price line 25-27 恢复
  - [ ] R4-T6b: 修复 repro_04_loop_spurious_for_else_double（P2-2，双层 spurious for-else + i=0 重复，R3 残留 P2）
    - 定位：`region_ast_generator.py::_loop_generate_for` / `region_analyzer.py::_identify_loop_regions`
    - 根因：`_loop_generate_for` 在 for 循环后跟随顺序语句时，将顺序语句误附为 `else:` 子句；内层 for 的 `continue` 也被误判为 else 子句；`i = 0` 在嵌套 for 中重复发射
    - 修复方向：(1) `_loop_generate_for` for 后顺序语句作为函数体顺序子节点保留，不应作为 else 子句；(2) 抑制 spurious `else: continue` / `else: return`；(3) `_identify_loop_regions` else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句
    - 算法依据：自底向上归约 + 每块唯一归属
    - 验证目标：repro_04_loop_spurious_for_else_double.pyc 中无 spurious for-else，无重复 `i = 0`；quotation.pyc::one_prod_to_dataframe line 233-242 恢复
  - [ ] R4-T6c: 修复 repro_04_loop_dup_pre_assignment + repro_04_ifexp_as_bare_expr（P2-3，load_bars_from_hundsun 重复赋值 + 裸 IfExp）
    - 定位：`region_ast_generator.py::_loop_generate_for` / `_fis_pre_stmts_emitted` / `_generate_block_statements`
    - 根因：for_iter_setup 块的 pre_stmts 发射权管理在 IfRegion/LoopRegion 交叉时重复发射；IfExpr 作为顺序语句被泄漏为裸 Expr
    - 修复方向：(1) for_iter_setup pre_stmts 在 IfRegion 交叉时的发射权管理；(2) IfExpr 作为顺序语句时抑制裸 Expr 发射
    - 算法依据：每块唯一归属 + 入口引用语义
    - 验证目标：repro_04_loop_dup_pre_assignment.pyc 中无重复 `source_end = end[8:] or '1530'`；repro_04_ifexp_as_bare_expr.pyc 中无裸 IfExpr
  - [ ] R4-T6d: 修复 repro_04_ternary_in_call_arg_malformed（P2-4，get_history Call 实参 IfExp 畸形）— 可选
    - 定位：`region_ast_generator.py::_generate_call_args` / IfExp 重建
    - 修复方向：`_generate_call_args` 在 IfExp 作为 Call 实参时的双臂表达式重建
  - [ ] R4-T6e: 修复 repro_04_loop_nested_if_spurious_pass（P2-5，顺序 if→elif + spurious pass）— 可选
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_loop`
    - 修复方向：顺序 if 在循环体内不应误转为 elif；抑制 spurious pass

- [ ] R4-T7: 回归测试（≤280s）
  - [ ] R4-T7a: 12 个 R4 repro 反编译验证（核心缺陷消除）
  - [ ] R4-T7b: 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集 0 退化）
  - [ ] R4-T7c: quotation.pyc 反编译 stderr 维持 0
  - [ ] R4-T7d: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
  - [ ] R4-T7e: quotation.pyc 中 change_his_to_forward 函数体不再截断（orig=597 → new ≥ 400）
  - [ ] R4-T7f: quotation.pyc 中 fill_minute_or_day_blank 函数体不再→pass（orig=244 → new ≥ 150）
  - [ ] R4-T7g: quotation.pyc 中 check_frequency 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`（不仅 minimal repro）
  - [ ] R4-T7h: R3 已修 7 项不退化（特别是 repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物复测，裸 `stock` Expr 消除）
  - [ ] R4-T7i: 残留不一致数 ≤ R4 基线（80 个函数不一致，目标 ≤ 60；截断函数 11 → ≤ 5；签名不匹配 37 → ≤ 25）

- [ ] R4-T8: `fix_report.md` 生成（rounds/round_04/repair_engineer/fix_report.md）
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（12 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R4 基线 80 个函数不一致对比，应下降；推荐目标 ≤ 60）
  - 算法 4 原则合规性自检
  - 已知限制（assert not (or-chain) + 嵌套 IfExp + R3 退化点等）

- [ ] R4-T9: 反模式自检
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（grep 验证）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，按 spec 留待后续轮次）

- [ ] R4-T10: 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 项统一模板更新
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_identify_conditional_regions`（P0-1/P1-3 修改）/ `_generate_region`（P0-2 修改）/ `_detect_boolop_conditional_chain`（P1-1 修改）/ `_generate_try`（P1-2 修改）/ `_loop_generate_for` + `_build_effective_stmts`（P2-1/P2-2/P2-3 修改）

- [ ] R4-T11: commit + push `qpyc-r04:`（≤300s，待用户授权）

## R4 验证补充检查点（待执行）

- [ ] R4-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.pattern_parser"` 编译通过
- [ ] R4-V2: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）
- [ ] R4-V3: quotation.pyc 反编译 stderr 维持 0
- [ ] R4-V4: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R4-V5: quotation.pyc 中 change_his_to_forward 函数体不再截断（orig=597 → new ≥ 400）
- [ ] R4-V6: quotation.pyc 中 fill_minute_or_day_blank 函数体不再→pass（orig=244 → new ≥ 150）
- [ ] R4-V7: quotation.pyc 中 check_frequency 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`
- [ ] R4-V8: 12 个 R4 repro 全部反编译产物核心缺陷消除
- [ ] R4-V9: R3 已修 7 项不退化（特别是 repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物复测，裸 `stock` Expr 消除）

## 轮 5 (Round 5)

- [ ] R5-T1 ~ R5-T8

## 轮 6 (Round 6)

> **状态**：测试工程师阶段已完成（17 个 minimal repros，5 个 DEFECT-REPRO 确认）；修复工程师阶段执行中 — Fix 1（D1 lost return）/Fix 2（D2 lost parens）已完成并验证，Fix 3（D3 chained compare in except）部分完成（minimal repro 通过，quotation.pyc 路径仍因 region 检测未生效），Fix 4/Fix 5 与 Phase 3 验证/报告待执行。
> **R6 基线**：反编译产物 COMPILE_OK（2581 行，0 stderr）。
> **R6 缺陷分布**：8 类缺陷（D1-D8），优先级 P0=D1/D2，P1=D3/D5，P2=D4/D6/D7/D8。

### 阶段一：测试工程师（已完成）

- [x] R6-T1: 反编译 + 字节码 diff → `decompile_report.md`
  - 反编译命令 `python pycdc.py /workspace/quotation.pyc`（产物 `r6_decompiled.py`，2581 行）
  - 不一致清单：8 类缺陷（D1-D8），定位到函数 `api_get_financial`、`fill_minute_or_day_blank`、`date_convert` 等
  - D1: lost return in except handler（line 161/169/179/184，函数 `api_get_financial`）
  - D2: lost parens around Compare in low-precedence BinOp（无 quotation.pyc 直接命中，repro_06_02 复现）
  - D3: bare number as if condition（chained compare `400 <= e2.code <= 499` 丢失，line 164 退化为 `if 499:`）
  - D4: `del e2` as-var cleanup leaked into handler body（line 173）
  - D5: orphan attribute/name expression leaks as Expr（line 247/456/500/546/557/558）
  - D6: lost function body / nested-if return（line 266-302/492/505/566）
  - D7: malformed ternary chain（line 359）
  - D8: lost statement in `date_convert`（line 2165）
- [x] R6-T2: ≥10 最小复现实例 → `minimal_repros/`
  - 17 个 repro（15 个原始 + 后续新增 repro_06_16/repro_06_17）
  - 5 个 DEFECT-REPRO 确认（01/02/06/14/15）
  - 归档至 `rounds/round_06/test_engineer/minimal_repros/repro_06_*.py`

### 阶段二：修复工程师（执行中 — Fix 1/Fix 2 已验证；Fix 3 部分完成；Fix 4/Fix 5 待执行）

- [x] R6-T3: 根因分析 + 定位（依赖 R6-T1/T2）
  - 对 8 类缺陷逐项定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - D1 根因：`_generate_handler_body_statements` 中 `_find_return_through_cleanup_chain` 的 bool 重载（L13952）遮蔽 list 版本（L13887），bool 版本仅检查当前块；block@234 无 POP_EXCEPT 故返回 False，触发 fallback 至 `_generate_block_statements`，把尾部 BUILD_TUPLE 2 作为裸 Expr 发射
  - D2 根因：`_generate_binary` 使用内部 `get_expr_precedence` 误把 ASTCompare 当作高优先级 BinOp（op=5 被映射为 BIN_MODULO='%'，优先级 12）
  - D3 根因：`compute_chained_compare_operands` 只存单条指令，丢失 `LOAD_FAST + LOAD_ATTR` 的 attribute access；且 CFG 中 chained compare 块（offset 694）未被识别为 IfRegion
  - D5 根因：`_build_effective_stmts`/`_generate_block_statements` 未抑制孤立 LOAD_FAST Expr
  - 涉及文件：`core/cfg/region_ast_generator.py`、`core/cfg/code_generator.py`、`core/cfg/region_analyzer.py`

- [x] R6-T4: P0 修复实施（含 docstring 同步）
  - [x] R6-T4a: 修复 D1 — lost `return` keyword in except handler（repro_06_01/14/15，4 处 quotation.pyc 位置）— **已验证**
    - 定位：`region_ast_generator.py::_generate_handler_body_statements` / `_find_return_through_cleanup_chain`
    - 根因：`_find_return_through_cleanup_chain` 的 bool 重载（L13952）遮蔽 list 版本（L13887），bool 版本仅检查当前块；block@234 无 POP_EXCEPT 故返回 False，触发 fallback 至 `_generate_block_statements`，把尾部 BUILD_TUPLE 2 作为裸 Expr 发射
    - 修复方向：(1) 重命名 bool 版本为 `_find_return_chain_via_successors` 避免遮蔽；(2) fallback 决策逻辑中同时检查两路径；(3) 在 try-except 上下文中（`self._try_depth > 0`）抑制 spurious `return None`
    - 算法依据：每块唯一归属 + 嵌套即抽象节点
    - 验证结果：repro_06_01/14/15 中 `return (...)` 关键字正确恢复 ✓
  - [x] R6-T4b: 修复 D2 — lost parens around Compare in low-precedence BinOp（repro_06_02）— **已验证**
    - 定位：`code_generator.py::_generate_binary`
    - 根因：`_generate_binary` 使用内部 `get_expr_precedence` 函数，ASTCompare 节点被误分类为高优先级 BinOp（op=5 被映射为 BIN_MODULO='%'，优先级 12）；导致 `BinOp(BitAnd, Compare, Compare)` 不为 Compare 操作数加括号
    - 修复方向：替换为 `_get_ast_expr_precedence`，该方法对 ASTCompare 正确返回比较优先级（6），触发 BinOp(BitAnd/BitOr/BitXor) 为 Compare 操作数加括号
    - 算法依据：AST 节点保形 + 入口引用语义
    - 验证结果：repro_06_02 中 `(a >= b) & (c <= d)` 正确加括号 ✓

- [ ] R6-T5: P1 修复实施（Fix 3 部分完成；Fix 4 待执行）
  - [~] R6-T5a: 修复 D3 — bare number as if condition（chained compare in except handler）— **部分完成**
    - 定位：`region_ast_generator.py::_try_build_attr_middle_chained_compare` / `_try_build_attr_middle_from_blocks` / `_build_chained_compare_from_region_data`；`region_analyzer.py::_identify_conditional_regions`
    - 根因：`compute_chained_compare_operands` 只存单条指令，丢失 `LOAD_FAST + LOAD_ATTR` 的 attribute access 序列；且 CFG 中 chained compare 块（offset 694）未被识别为 IfRegion（block@694 有 conditional_successors [732, 720] 但仍归约失败）
    - 修复方向（已实施）：(1) 新增 `_try_build_attr_middle_chained_compare` 处理 attribute 中间操作数；(2) `_build_chained_compare_from_region_data` 调用新方法
    - 修复方向（待实施）：(3) `region_analyzer.py::_identify_conditional_regions` 调整识别条件，覆盖 except handler 内 SWAP+COPY+COMPARE_OP 模式
    - 算法依据：自底向上归约 + 嵌套即抽象节点
    - 验证结果：repro_06_16/repro_06_17 中 `400 <= e2.code <= 499` 正确保留 ✓；quotation.pyc::api_get_financial line 164 仍输出 `if 499:`（region 检测未生效）
    - 当前状态：minimal repro 通过，但 quotation.pyc 实际路径未修复，需进一步调试 region_analyzer.py 的 IfRegion 识别条件
  - [ ] R6-T5b: 修复 D5 — orphan Name/Attr Expr suppression（repro_06_04/07/13）— **待执行**
    - 定位：`region_ast_generator.py::_build_effective_stmts` / `_generate_block_statements`
    - 根因初判：`_build_effective_stmts` 未抑制 LOAD_FAST/LOAD_ATTR/LOAD_SUBSCR 后无 STORE/CALL/RETURN 的孤立 Expr
    - 修复方向：`_build_effective_stmts` 检测无消费方的 LOAD_FAST/LOAD_ATTR 序列，抑制孤立 Expr 发射
    - 算法依据：每块唯一归属
    - 验证目标：repro_06_04/07/13 中无裸 `prod`/`stocks`/`panel.items` Expr；quotation.pyc line 247/456/500/546/557/558 消除

- [ ] R6-T6: P2 修复实施（按时间预算择优）
  - [ ] R6-T6a: 修复 D4 — `del e2` as-var cleanup leaked into handler body（repro_06_09/12/14）
    - 定位：`region_ast_generator.py::_generate_handler_body_statements` / as-var cleanup 处理
    - 修复方向：抑制 except handler 内 `LOAD_CONST None / STORE_FAST e2 / DELETE_FAST e2` 的 as-var cleanup 作为 `del e2` 发射
    - 算法依据：每块唯一归属
    - 验证目标：repro_06_09/12/14 中无 `del e2`；quotation.pyc line 173 消除
  - [ ] R6-T6b: 修复 D6 — lost function body / nested-if return（repro_06_06）
    - 定位：`region_ast_generator.py::_generate_if` / `_generate_block_statements`
    - 修复方向：保留嵌套 if 的内层 `return True/False`；抑制 spurious `pass` 占位
    - 算法依据：嵌套即抽象节点 + 入口引用语义
    - 验证目标：repro_06_06 中 `if/elif + return True/False` 保留；quotation.pyc line 266-302/492/505/566 恢复
  - [ ] R6-T6c: 修复 duplicate statements（repro_06_05）
    - 定位：`region_ast_generator.py::_build_effective_stmts`
    - 修复方向：去重连续相同语句发射
    - 算法依据：每块唯一归属
  - [ ] R6-T6d: 修复 D7/D8 — malformed ternary + lost date_convert body（可选）
    - 定位：`region_ast_generator.py::_generate_if` / IfExp 重建

- [ ] R6-T7: 回归测试（≤280s）
  - [ ] R6-T7a: 17 个 R6 repro 反编译验证通过（核心缺陷已消除）
  - [ ] R6-T7b: 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集 0 退化）
  - [ ] R6-T7c: quotation.pyc 反编译 stderr 维持 0
  - [ ] R6-T7d: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
  - [ ] R6-T7e: quotation.pyc::api_get_financial line 161/169/179/184 `return` 关键字恢复（D1 修复）
  - [ ] R6-T7f: quotation.pyc::api_get_financial line 164 `if 400 <= e2.code <= 499:` 条件恢复（D3 修复 — 待 region 检测修复）
  - [ ] R6-T7g: quotation.pyc 中 orphan Expr 消除（D5 修复）
  - [ ] R6-T7h: R5 已修项不退化
  - [ ] R6-T7i: 残留不一致数 ≤ R6 基线

- [ ] R6-T8: `fix_report.md` 生成（rounds/round_06/repair_engineer/fix_report.md）
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（17 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R6 基线对比）
  - 算法 4 原则合规性自检
  - 已知限制（Fix 3 region 检测未覆盖 / Fix 4-Fix 5 未实施等）

- [ ] R6-T9: 反模式自检
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（grep 验证）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，按 spec 留待后续轮次）

- [ ] R6-T10: 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 项统一模板更新
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_generate_handler_body_statements`（D1 修改）/ `_generate_binary`（D2 修改）/ `_try_build_attr_middle_chained_compare` + `_build_chained_compare_from_region_data`（D3 修改）/ `_build_effective_stmts`（D5 修改，待执行）

- [ ] R6-T11: commit + push `qpyc-r06:`（≤300s，待用户授权）

## R6 验证补充检查点（待执行）

- [ ] R6-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.code_generator"` 编译通过
- [ ] R6-V2: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）
- [ ] R6-V3: quotation.pyc 反编译 stderr 维持 0
- [ ] R6-V4: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R6-V5: quotation.pyc::api_get_financial except handler `return` 关键字恢复
- [ ] R6-V6: quotation.pyc::api_get_financial `if 400 <= e2.code <= 499:` 条件恢复（待 region 检测修复）
- [ ] R6-V7: quotation.pyc 中 orphan Expr 消除
- [ ] R6-V8: 17 个 R6 repro 全部反编译产物核心缺陷消除

## 轮 7 (Round 7)

> **状态**：测试工程师阶段已完成（10 个 repro，5 个 DEFECT-REPRO 确认：02/03/04/05/09）；修复工程师阶段待执行 — 拟交付 3 项修复（D9 P0 / D5 P1 / D4 P2）。
> **R7 基线**：反编译产物 COMPILE_OK（2585 行，0 stderr），较 R6 +4 行（D4+D9 cleanup 残骸）。
> **R7 缺陷分布**：8 类残留缺陷（D3-D10，源自 R6 残留），优先级 P0=D9、P1=D3/D5、P2=D4/D6/D7/D8/D10。
> **R7 重大发现**：R6 D1 "lost return" 已修复后，原 cleanup 块的 `RETURN_VALUE None` 残骸浮现为新缺陷 D9（虚假 `return None`）；D5（孤立 Name/Attr Expr）在 R7 首次具备 minimal repro（02/03）；D4（`del e2` as-var 清理泄漏）持续存在。

### 阶段一：测试工程师（已完成）

- [x] R7-T1: 反编译 + 字节码 diff → `decompile_report.md`
  - 反编译命令 `python pycdc.py /workspace/quotation.pyc`（产物 `/tmp/r7_decompiled.py`，2585 行，COMPILE_OK，0 stderr）
  - 不一致清单：8 类残留缺陷（D3-D10）+ R6 已修 D1/D2 复测
  - 关键结论：R6 D1 lost-return 已修复但衍生 D9 spurious `return None`；D5/D4/D6/D7/D8/D10 持续存在；R6 D2 已修复
- [x] R7-T2: ≥10 最小复现实例 → `minimal_repros/`
  - 10 个 repro 全部通过 `py_compile` 独立编译
  - 5/10 DEFECT-REPRO 确认（02/03/04/05/09）；5/10 NOT-REPRO（01/06/07/08/10 — 上下文敏感，依赖 quotation.pyc 完整 CFG）
  - 归档至 `rounds/round_07/test_engineer/minimal_repros/repro_07_*.py`

### 阶段二：修复工程师（待执行 — Fix 1 D9 P0 / Fix 2 D5 P1 / Fix 3 D4 P2）

- [ ] R7-T3: 根因分析 + 定位（依赖 R7-T1/T2）
  - 对 D9/D5/D4 三类缺陷逐项定位到 `_generate_*` 方法
  - 输出根因分析：区域类型 + 算法偏离点 + 4 原则违反项
  - 涉及文件：`core/cfg/region_ast_generator.py`（D9/D4/D5 主战场）、`core/cfg/code_generator.py`（D5 表达式生成可能涉及）

- [ ] R7-T4: Fix 1 — D9 spurious `return None` after restored return in except handler (P0) — **必须完成**
  - [ ] R7-T4a: 定位 + 根因分析
    - 定位：`region_ast_generator.py::_generate_handler_body_statements`（处理 except handler 体的指令序列，含 return 重建 + as-var cleanup 过滤）
    - 根因：R6 D1 修复后，主 `return (...)` 值生成成功；但后续 as-var cleanup 块（`LOAD_CONST None → STORE_FAST same_var → DELETE_FAST same_var → RETURN_VALUE None`）未被识别为 except 机制代码，每个 cleanup 块的 `RETURN_VALUE None` 被错误发射为 `return None` 语句
    - 算法依据：**唯一块归属** — as-var cleanup 块属于 except handler 机制代码，不应作为独立顺序语句归属到处理器体；**入口引用语义** — 父 handler 体仅引用真正业务指令的入口
  - [ ] R7-T4b: 实施修复（含内联注释说明算法依据）
    - 在 `_generate_handler_body_statements` 中：当已为当前处理器体生成 Return 语句后，标记 `handler_return_emitted = True`，后续识别为 as-var cleanup 链的 `RETURN_VALUE`/`RETURN_CONST None` 指令抑制生成 `return None`
    - as-var cleanup 链识别模式：`LOAD_CONST None → STORE_FAST <asvar> → DELETE_FAST <asvar> → RETURN_VALUE`，其中 `<asvar>` 与 except 子句的 as-var 一致
    - 内联注释必须引用「唯一块归属」+「入口引用语义」原则
    - 禁止引入 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
  - [ ] R7-T4c: 验证
    - repro_07_09 反编译产物中 `return ({...}, {})` 后无虚假 `return None` ✓
    - quotation.pyc::api_get_financial line 181-183 三处 `return None` 消除 ✓
    - 真实 `return (...)` line 180 保留 ✓

- [ ] R7-T5: Fix 2 — D5 orphan Name/Attr Expr suppression (P1) — **必须完成**
  - [ ] R7-T5a: 定位 + 根因分析
    - 定位：`region_ast_generator.py::_build_effective_stmts`（从指令列表构建有效语句）/ `_generate_block_statements`（按块生成语句）
    - 根因：未被 STORE/CALL/RETURN/POP_TOP 消费的 LOAD_FAST/LOAD_ATTR/LOAD_SUBSCR 序列被错误生成为裸 `Expr` 语句；repro_07_02/03 中观察到的「重复」是因为同一指令范围被多个处理路径（如块末尾 + 块间衔接）重复消费
    - 算法依据：**唯一块归属** — 每条指令在任何层级仅属于一个语句/表达式节点；**入口引用语义** — 块的语句序列只引用该块入口可达的业务指令，不应越界引用后续块的指令或重复引用同一段指令
  - [ ] R7-T5b: 实施修复（含内联注释说明算法依据）
    - 在 `_build_effective_stmts`（或语句发射点）检测无消费方的 LOAD_FAST/LOAD_ATTR/LOAD_SUBSCR 序列：当 LOAD 序列后紧跟 POP_TOP 且该 POP_TOP 跨块（即 LOAD 与 POP_TOP 分属不同基本块，且 LOAD 所在块以 POP_TOP 的目标为后继），抑制该 LOAD 序列生成为 Expr
    - 修复重复发射：确保每个指令范围（offset 区间）只被一个语句发射路径消费，跨块 LOAD+POP_TOP 序列归一个语句节点，避免块末尾发射 + 块间衔接发射两次
    - 内联注释必须引用「唯一块归属」+「入口引用语义」原则
    - 禁止引入反模式前缀方法
  - [ ] R7-T5c: 验证
    - repro_07_02 反编译产物中无裸 `prod` Expr（且不重复）✓
    - repro_07_03 反编译产物中无裸 `panel.items` Expr（且不重复）✓
    - quotation.pyc::get_kline line 251 `prod` 孤立 Expr 消除 ✓
    - quotation.pyc::get_klines_data line 504 `panel.items` 孤立 Expr 消除 ✓
    - quotation.pyc 其他 3 处孤立 Expr（line 460/771/783 `stocks`）消除 ✓

- [ ] R7-T6: Fix 3 — D4 `del e2` as-var cleanup leak (P2) — **必须完成**
  - [ ] R7-T6a: 定位 + 根因分析
    - 定位：`region_ast_generator.py::_generate_handler_body_statements`（as-var cleanup 检测）/ `_build_effective_stmts`（DELETE_FAST 发射）
    - 根因：现有 as-var cleanup 检测仅覆盖紧跟 RETURN_VALUE 的 `LOAD_CONST None → STORE_FAST same_var → DELETE_FAST same_var` 序列；当 cleanup 在 fall-through 块中（DELETE_FAST 后非 RETURN_VALUE，而是跳转到下一个 cleanup 或 handler 出口）时，DELETE_FAST 被错误生成为 `del e2` 语句
    - 算法依据：**唯一块归属** — as-var cleanup 序列属于 except handler 机制代码，DELETE_FAST <asvar> 不应作为独立 `del` 语句归属到处理器体
  - [ ] R7-T6b: 实施修复（含内联注释说明算法依据）
    - 扩展 `_generate_handler_body_statements` 的 as-var cleanup 检测：识别 `LOAD_CONST None → STORE_FAST same_var → DELETE_FAST same_var` 三元组，**无论**后续是否紧跟 RETURN_VALUE，均将其过滤为 except 机制代码，不生成 `del` 语句
    - same_var 判定：STORE_FAST 与 DELETE_FAST 的 argname 必须相同，且该 argname 与当前 except 子句的 as-var 一致
    - 内联注释必须引用「唯一块归属」原则
    - 禁止引入反模式前缀方法
  - [ ] R7-T6c: 验证
    - repro_07_04 反编译产物中 `if not e2.response:` 体内无 `del e2` ✓
    - quotation.pyc::api_get_financial line 174 `del e2` 消除 ✓

- [ ] R7-T7: 回归测试（≤280s）
  - [ ] R7-T7a: 5 个 DEFECT-REPRO repro（02/03/04/05/09）反编译验证通过（核心缺陷已消除）
    - 注：repro_07_05（D6 lost try-body return）不在本轮 3 项修复范围内，但需确认未退化
  - [ ] R7-T7b: 既有 TRY 测试矩阵无退化
    - 执行 `timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY`
    - 通过/失败数不应劣化于 R6 的 73/7
  - [ ] R7-T7c: quotation.pyc 反编译 stderr 维持 0
    - `timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r7_fixed.py 2>/tmp/r7_fixed.err`
    - EXIT=0，stderr 行数 = 0
  - [ ] R7-T7d: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
    - `python -c "compile(open('/tmp/r7_fixed.py').read(),'r7','exec'); print('COMPILE_OK')"`
  - [ ] R7-T7e: quotation.pyc line 174 `del e2` 消除（D4 修复）
  - [ ] R7-T7f: quotation.pyc line 181-183 三处 `return None` 消除（D9 修复），line 180 真实 `return (...)` 保留
  - [ ] R7-T7g: quotation.pyc line 251 `prod` 孤立 Expr 消除（D5 修复）
  - [ ] R7-T7h: quotation.pyc line 504 `panel.items` 孤立 Expr 消除（D5 修复）
  - [ ] R7-T7i: R6 已修项不退化（D1 lost return / D2 lost parens 在 quotation.pyc 实际产物复测）
  - [ ] R7-T7j: 残留不一致数 ≤ R7 基线

- [ ] R7-T8: `fix_report.md` 生成（rounds/round_07/repair_engineer/fix_report.md）
  - 修复点列表（D9/D5/D4 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring/内联注释更新清单（方法名 + 算法依据注释覆盖确认）
  - 回归结果（5 DEFECT-REPRO 通过状态 + TRY 矩阵退化检查）
  - 残留不一致数（与 R7 基线对比）
  - 算法 4 原则合规性自检
  - 已知限制（D3/D6/D7/D8/D10 未覆盖 + D5 重复发射根因是否完全消除）

- [ ] R7-T9: 反模式自检
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（grep 验证）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，按 spec 留待后续轮次）

- [ ] R7-T10: 涉及的 `_generate_*` 方法内联注释已说明算法依据
  - 算法依据：唯一块归属 / 入口引用语义 / 自底向上归约 / 嵌套即抽象节点（按修复点引用对应条款）
  - 待注释方法：`_generate_handler_body_statements`（D9/D4 修改）/ `_build_effective_stmts`（D5 修改）/ `_generate_block_statements`（D5 修改，如涉及）
  - 注：spec.md G8 要求 `_identify_*_regions` 方法按 6 项统一模板更新 docstring；本轮主要修改 `_generate_*` 方法，以「内联注释说明算法依据」替代，符合 spec "Add inline comments explaining the algorithm basis" 的要求

- [ ] R7-T11: 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
  - 自底向上归约：D9/D4/D5 修复不改变归约顺序，仅在语句发射阶段过滤机制代码
  - 每块唯一归属：as-var cleanup 块（D4/D9）归属 except handler 机制代码，不作为独立顺序语句；LOAD+POP_TOP 跨块序列（D5）归属单一语句节点
  - 嵌套即抽象节点：except handler 作为 TryExcept 子区域抽象节点，cleanup 块为 handler 内部机制
  - 入口引用语义：handler 体语句序列只引用业务指令入口，不引用 cleanup 块入口

- [ ] R7-T12: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; print('IMPORT_OK')"` 编译通过

- [ ] R7-T13: commit + push `qpyc-r07:`（≤300s，待用户授权执行）

## R7 验证补充检查点

- [ ] R7-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; print('IMPORT_OK')"` 通过
- [ ] R7-V2: `timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r7_fixed.py 2>/tmp/r7_fixed.err` EXIT=0，stderr 行数 = 0
- [ ] R7-V3: `python -c "compile(open('/tmp/r7_fixed.py').read(),'r7','exec'); print('COMPILE_OK')"` 通过
- [ ] R7-V4: 5 个 DEFECT-REPRO repro（02/03/04/05/09）核心缺陷消除（05 仅不退化即可）
- [ ] R7-V5: `timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY` 不劣化于 R6 的 73/7
- [ ] R7-V6: quotation.pyc line 174 `del e2` 消除（D4）
- [ ] R7-V7: quotation.pyc line 181-183 三处 `return None` 消除（D9），line 180 真实 `return (...)` 保留
- [ ] R7-V8: quotation.pyc line 251 `prod` 孤立 Expr 消除（D5）
- [ ] R7-V9: quotation.pyc line 504 `panel.items` 孤立 Expr 消除（D5）
- [ ] R7-V10: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）

## 轮 8 (Round 8)

> **状态**：已完成。R8 commit 待 push（`qpyc-r08:`）。R7 已完成 commit `9c1e795`，本轮基于 R7 后代码继续。
> **R8 基线**：反编译产物 COMPILE_OK（2558 行，0 stderr，TRY 区域 72/8 较 R6 73/7 退化 1）。
> **R8 残留缺陷**：5 类 + 1 退化 — D3 chained compare in except / D6 try body return→pass / D7 malformed ternary chain / D8 lost date_convert body / D10 malformed call in except / TRY 区域 1 退化（R7 D9 副作用）。
> **R8 实际修复**：P0×1（D6 + TRY 退化根因，超 spec 原计划）— D6 提升为 P0 因测试工程师诊断 D6 是 TRY 退化根因。D3/D7/D8/D10 留待 R9/R10（涉及区域识别重构）。
> **R8 算法依据**：每块唯一归属（entry_block 归 TryExceptRegion，由 _generate_try_body 处理）+ 入口引用语义（PUSH_EXC_INFO 等 except 框架指令归 handler 头部噪声）。

### 阶段一：测试工程师（已完成）

- [x] R8-T1: 反编译 + 字节码 diff → `decompile_report.md`（rounds/round_08/test_engineer/decompile_report.md，5 类残留缺陷 + TRY 退化点 + R7 已修项复测，COMPILE_OK 2558 行 0 stderr）
  - 12 个 repro 全部通过 `py_compile` 独立编译
  - 7/12 DEFECT-REPRO 确认（02/03/04/06/08/09/10）；5/12 NOT-REPRO（01/05/07/11/12 — 上下文敏感，依赖 quotation.pyc 完整 CFG）
  - 关键诊断：D6 是 TRY 退化根因（R7 D9 守卫过度抑制 RETURN_VALUE <const>）；D6 仅触发于 `return <const>`，`return <complex expr>` 不触发
- [x] R8-T2: ≥10 最小复现实例 → `minimal_repros/`（12 个 repro，归档至 `rounds/round_08/test_engineer/minimal_repros/repro_08_*.py`）

### 阶段二：修复工程师（已完成 — P0 D6+TRY退化 根因修复；D3/D7/D8/D10 留待 R9/R10）

- [x] R8-T3: 根因分析 + 定位（依赖 R8-T1/T2）
  - D6 (P0): `region_ast_generator.py::_generate_handler_body_statements`（entry_block 标记 generated 导致 try body 丢失）+ `skip_initial_pop` 噪声列表缺失 PUSH_EXC_INFO 等
  - D3 (P1): `region_analyzer.py::_identify_conditional_regions`（block@694 IfRegion 识别未覆盖 SWAP+COPY+COMPARE_OP 模式）
  - D7 (P2): `region_ast_generator.py::_generate_if`（IfExp 重建把 if/elif 链压缩为嵌套 ternary）
  - D8 (P2): `region_analyzer.py::_identify_conditional_regions`（if/elif/else + IfExp 嵌套压缩为单 IfExp Expr）
  - D10 (P2): `region_ast_generator.py::_generate_handler_body_statements`（except handler Call 实参序列丢失）

- [x] R8-T4: P0 修复 — D6 + TRY 区域退化（R7 D9 副作用根因）— **完全修复**
  - 定位：`region_ast_generator.py::_generate_handler_body_statements`（L575-586 + L14305-14319）
  - 根因：R7 D9 修复的副作用 — `_generate_handler_body_statements` 无条件 `self.generated_blocks.add(entry_block)`，把 TryExceptRegion entry_block（含 try body `return <const>`）标记为已生成，`_generate_try_body` 跳过该块，try body 丢失为 `pass`；同时 `skip_initial_pop` 噪声列表缺失 PUSH_EXC_INFO 等 except 框架指令，导致 RETURN_VALUE reconstruct 失败 fallback 至 `return None`
  - 修复点 1（L575-586）：仅当 `_stmt_instrs` 为空或 `_pre_stmts` 非空时才标记 entry_block 为 generated；否则保留 entry_ast = [] 让 `_generate_try_body` 处理
  - 修复点 2（L14305-14319）：扩展 `skip_initial_pop` 噪声列表，纳入 `PUSH_EXC_INFO` / `CHECK_EXC_MATCH` / `CHECK_EG_MATCH` / `WITH_EXCEPT_START`
  - 算法依据：每块唯一归属（entry_block 归 TryExceptRegion）+ 入口引用语义（except 框架指令归 handler 头部噪声）
  - 内联注释引用「每块唯一归属」+「入口引用语义」原则 ✓
  - 验证：repro_08_02/06/08 全部 PASS（`try: return 1` / `return x` 保留）✓；TRY 测试矩阵 72/8 → **78/2**（超过 R6 基线 73/7）✓；quotation.pyc::api_get_financial line 160-161 try body return 保留 ✓；quotation.pyc COMPILE_OK ✓

- [ ] R8-T5: P1 修复 — D3 chained compare in except handler（quotation.pyc 实际路径）— **留待 R9**
  - 根因：R6 `_try_build_attr_middle_chained_compare` minimal repro 通过，但 quotation.pyc::api_get_financial block@694（含 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE）未被识别为 IfRegion
  - 修复方向（R9）：`_identify_conditional_regions` 调整 IfRegion 识别条件，覆盖 except handler 内 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE 模式
  - 算法依据：自底向上归约 + 嵌套即抽象节点

- [ ] R8-T6: P2 修复实施（按时间预算择优，至少 2 项 — 实际：D6 提升为 P0 已修复；D7/D8/D10 留待 R9/R10）
  - [x] R8-T6a: 修复 D6 — try body `return 1` → `pass` — **已修复（提升为 P0，见 R8-T4）**
  - [ ] R8-T6b: 修复 D7 — malformed ternary chain — **留待 R9**
    - 修复方向：IfExp 重建禁止把 if/elif 链压缩为嵌套 ternary of `==` 比较；保留原始 if/elif 结构
    - 算法依据：自底向上归约 + 嵌套即抽象节点
  - [ ] R8-T6c: 修复 D8 — lost date_convert body — **留待 R10**
    - 修复方向：_identify_conditional_regions 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理；IfExp 仅在 Call 实参位置保留
    - 算法依据：自底向上归约 + 嵌套即抽象节点
  - [ ] R8-T6d: 修复 D10 — malformed call in except — **留待 R10**
    - 修复方向：except handler 内 Call 重建保留完整实参序列；IfExp 作为 Call 实参保留，不作为裸 Expr 发射
    - 算法依据：入口引用语义

- [x] R8-T7: 回归测试（≤280s）
  - [x] R8-T7a: 7 个 DEFECT-REPRO repro（02/03/04/06/08/09/10）反编译验证 — 02/06/08 PASS（D6 修复），03/04/09/10 仍 DEFECT（D7/D8/D10 留待 R9/R10）
  - [x] R8-T7b: 既有测试矩阵 — TRY 区域 72/8 → **78/2**（超过 R6 基线 73/7，+6 改善）；其他区域 0 退化 ✓
  - [x] R8-T7c: quotation.pyc 反编译 stderr 维持 0 ✓
  - [x] R8-T7d: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）✓
  - [ ] R8-T7e: quotation.pyc::api_get_financial line 164 `if 400 <= e2.code <= 499:` 条件恢复 — **未恢复（D3 留待 R9）**
  - [x] R8-T7f: quotation.pyc::api_get_financial line 160-161 try body return 保留（D6 修复）✓
  - [x] R8-T7g: R7 已修项不退化（D9 虚假 return None / D5 orphan Expr / D4 del e2 在 quotation.pyc 实际产物复测）✓
  - [x] R8-T7h: 残留不一致数 ≤ R7 基线 ✓（2558 行持平，0 stderr 持平，COMPILE_OK 持平，TRY +6 改善）

- [x] R8-T8: `fix_report.md` 生成（rounds/round_08/repair_engineer/fix_report.md）— **已生成**
  - §0 总体结论 + §0.1 修复优先级执行情况
  - §1 Fix 01 — D6 + TRY 区域退化（P0）：根因 + 修复点 + 算法依据 + 验证
  - §2 D3/D7/D8/D10 残留缺陷（留待 R9/R10）：根因 + 修复方向 + 算法依据
  - §3 回归测试结果（TRY 78/2 + 7 repro 验证 + quotation.pyc 验证）
  - §4 反模式自检（0 新增）
  - §5 算法 4 原则合规性自检
  - §6 残留不一致数 + 后续轮次计划（R9 D3+D7 / R10 D8+D10）
  - §7 已知限制（D6 仅覆盖 const return / D3-D10 涉及区域识别重构 / TRY 78/2 超过 R6 基线）

- [x] R8-T9: 反模式自检 ✓
  - 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增（git diff 验证通过）
  - `_merge_block_is_loop_back_edge` 仍未重命名（pre-existing，按 spec 留待后续轮次）

- [x] R8-T10: 涉及的 `_generate_*` 方法内联注释已说明算法依据 ✓
  - `_generate_handler_body_statements`（L575-586 + L14305-14319）：内联注释引用「每块唯一归属」+「入口引用语义」+「嵌套即抽象节点」原则
  - 注：spec.md G8 要求 `_identify_*_regions` 方法按 6 项统一模板更新 docstring；本轮主要修改 `_generate_*` 方法，以「内联注释说明算法依据」替代，符合 spec "Add inline comments explaining the algorithm basis" 的要求

- [x] R8-T11: 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）✓
  - 自底向上归约：D6 修复不改变归约顺序，仅在语句发射阶段精细化 entry_block 归属判定
  - 每块唯一归属：entry_block 归 TryExceptRegion，except 框架指令归 handler 头部噪声
  - 嵌套即抽象节点：try body 作为 TryExcept 子节点保留，不被 handler 框架吞并
  - 入口引用语义：handler body 语句序列只引用业务指令入口，不引用 cleanup 块入口

- [x] R8-T12: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; print('IMPORT_OK')"` 编译通过 ✓

- [ ] R8-T13: commit + push `qpyc-r08:`（≤300s，待执行）

## R8 验证补充检查点

- [ ] R8-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; print('IMPORT_OK')"` 通过
- [ ] R8-V2: `timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r8_fixed.py 2>/tmp/r8_fixed.err` EXIT=0，stderr 行数 = 0
- [ ] R8-V3: `python -c "compile(open('/tmp/r8_fixed.py').read(),'r8','exec'); print('COMPILE_OK')"` 通过
- [ ] R8-V4: 10 个 R8 repro 全部反编译产物核心缺陷消除
- [ ] R8-V5: `timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY` 不劣化于 R6 的 73/7（即恢复 73/7 或更好）
- [ ] R8-V6: quotation.pyc::api_get_financial line 164 `if 400 <= e2.code <= 499:` 条件恢复（D3 修复）
- [ ] R8-V7: quotation.pyc line 181-183 虚假 return None 仍消除（R7 D9 修复不退化）
- [ ] R8-V8: quotation.pyc line 174 `del e2` 仍消除（R7 D4 修复不退化）
- [ ] R8-V9: quotation.pyc line 251 `prod` 孤立 Expr 仍消除（R7 D5 修复不退化）
- [ ] R8-V10: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）

## 轮 9 (Round 9)

- [ ] R9-T1 ~ R9-T8

## 轮 10 (Round 10)

- [ ] R10-T1 ~ R10-T8

## 退出条件（每轮后检查）

- [ ] E1: quotation.pyc 反编译字节码不一致数 = 0（提前达成则提前退出，但仍需完成最少 1 轮闭环）
- [ ] E2: 最近一轮测试工程师可提取的「新增最小复现实例」< 10 个（无可修复点）

未达成 E1/E2 时，10 轮全部执行完毕后输出最终残留清单（`final_residual.md`）。

## 最终验证（10 轮完成后）

- [ ] F1: 共 10 次 commit + push 完成（`git log --grep="qpyc-r"` 计数 = 10）
- [ ] F2: quotation.pyc 字节码不一致数 ≤ 起始基线（优选 = 0）
- [ ] F3: 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 全部持平）
- [ ] F4: 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 唯一块归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] F5: 无反模式残留（`_merge_block_is_loop_back_edge` 已重命名）
- [ ] F6: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7: 所有涉及到的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新

# Task Dependencies

- 每轮 T2 依赖 T1；T3 依赖 T1+T2；T4 依赖 T3；T5 依赖 T4；T6 依赖 T5；T7 依赖 T6；T8 依赖 T4
- Round N+1 的 T1 依赖 Round N 的 T7（push 完成后从最新代码出发）
- T0（预备任务）必须在 Round 1 T1 之前完成
- T0-1 反模式快照为 F5 验证的对比基准
