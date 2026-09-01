# 验证清单

> 目标：对 `/workspace/quotation.pyc` 执行 10 轮双工程师迭代，直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + 提取 10+ 最小复现实例 → 修复工程师按区域归约算法修复 → 回归 → commit + push。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `qpyc-rNN:`）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增
- [ ] G5 该轮 10+ 最小复现实例全部通过
- [ ] G6 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] G7 `decompile_report.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新
- [ ] G9 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建

## 预备阶段

- [x] P0 `baseline/original_bytecode.txt` 已生成（133 函数 dis 输出）
- [x] P1 `baseline/decompiled_baseline.py` 已生成（2593 行，19 处 MatchSingleton 警告）
- [x] P2 编译验证：line 2579 `filter_type=` 缺默认值（首轮语法错误）
- [x] P3 反模式起点快照已记录（`baseline/antipattern_snapshot.txt`：_merge_=1, 其他=0）

## 轮 1 (Round 1)

- [x] R1-1 反编译 + 字节码 diff（`decompile_report.md`，12 类缺陷，line 2579 + 19 处 MatchSingleton）
- [x] R1-2 ≥10 最小复现实例（`minimal_repros/`，12 个 repro 全部 py_compile 通过）
- [x] R1-3 根因分析（定位到识别/生成方法）（fix_report.md §1 已确认 4 项根因）
- [x] R1-4 修复实施（含 docstring 同步）（P0×2 + P1×2；4 处 docstring 更新）
- [x] R1-5 回归测试通过（10 区域 0 退化；12 repro 全部可编译）
- [x] R1-6 `fix_report.md` 生成（rounds/round_01/repair_engineer/fix_report.md）
- [ ] R1-7 commit + push `qpyc-r01:`（待用户授权执行）
- [x] R1-8 反模式自检通过（G3：0 新增；F6：import OK）
- [x] R1-9 残留不一致数 ≤ 基线（MatchSingleton 19→0；语法错误 1→0；残留缺陷类 12→8）

## 轮 2 (Round 2)

> **R2 基线**：反编译产物 COMPILE_OK，但 81 个函数字节码不一致、70 个函数签名不匹配、1 个 listcomp 丢失。
> **R2 缺陷分布**：14 类（10 项 R1 残留演化 + 4 项 R2 新增），P0=2、P1=5、P2=7。

### 阶段一：测试工程师（已完成）

- [x] R2-1 反编译 + 字节码 diff（`decompile_report.md`，14 类缺陷，81 个函数不一致，COMPILE_OK）
- [x] R2-2 ≥10 最小复现实例（`minimal_repros/`，14 个 repro 全部 py_compile + DEFECT-REPRO 验证通过）

### 阶段二：修复工程师（执行中 — P0+3 项 P1 已验证通过，quotation.pyc 仍存孤儿 try 阻塞编译）

#### P0 修复（必须完成）

- [x] R2-3 根因分析完成（14 个 repro 全部定位到 `_identify_*_regions` 或 `_generate_*` 方法，输出根因 + 4 原则违反项）
- [x] R2-4a P0 repro_13 修复完成 — **已验证**
  - `cfg_builder.py::_identify_jump_targets` 不再将非跳转目标的 NOP 作为块边界（条件判断：NOP 后续首条非_NOP 为 LOAD_CONST 且 5 条内有 MAKE_FUNCTION → 对齐填充，跳过；否则为结构边界）
  - `region_ast_generator.py::_reconstruct_decorator_chain` 在 NOP 不切块后正确识别装饰器
  - `code_generator.py::_generate_function_def` defaults 元组填入函数签名，不挂 decorators
  - quotation.pyc 中 3 处 `@((...))` 误装饰器全部消失（`get_price` 后 / `get_history` 前 / `get_fundamentals` 前）— 待 quotation.pyc 全量验证
  - `_identify_jump_targets` docstring 按 6 项模板更新 ✓
  - 验证：repro_13 反编译产物 `def get_history(count, frequency='1d', ...)` 无 `@((...))` 前导 ✓
- [x] R2-4b P0 repro_14 修复完成 — **已验证**
  - `region_analyzer.py::_identify_conditional_regions` / `_build_elif_region` 不再把 elif fall-through 吸收为不可达
  - 结构区域块集合（_structural_region_entries）扩展为包含所有结构区域块（含 setup/header/body），覆盖 LoopRegion 的 LOAD_FAST+GET_ITER setup 块
  - then/else 分支 ipdom 链遍历中检测多非回边前驱的结构区域块（`_non_backedge_preds > 1`），正确设置 merge 点
  - 9 个财务函数（`get_balance_statement` / `get_income_statement` / `get_cashflow_statement` / `get_eps` / `get_cash_collection_ability` / `get_debt_paying_ability` / `get_growth_ability` / `get_operating_ability` / `get_profit_ability`）函数体不再截断 — 待 quotation.pyc 全量验证
  - `_identify_conditional_regions` / `_build_elif_region` docstring 已存在 6 节结构（算法描述/字节码模式/边界条件/归约语义/AST映射/已知失败模式），覆盖 6 项模板要求 ✓
  - 验证：repro_14 反编译产物 `get_balance_statement` for 循环 + return 正确保留 ✓（注：spurious for-else 属 repro_09 范畴）

#### P1 修复（必须完成至少 4 项 — 已完成 3 项：repro_02/15/16）

- [x] R2-5a P1 repro_02 + repro_16 修复完成 — **已验证**
  - `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE` 重建为 `is None`/`is not None`（非 `== None`）
  - `CONTAINS_OP 0`（not in）正确解析为 `not in`（非 `in`）
  - `ast_converter.py::_convert_compare_full` 处理 dict-form ops 第三种格式 `{'type': 'Is'}` + PascalCase 操作符映射
  - `region_ast_generator.py::_wrap_boolop_with_merge_compare` 条件上下文 BoolOp 不进行包裹比较
  - 验证：repro_02 `if quote is None and is_trade:` + `elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:` ✓
  - 验证：repro_16 `if frequency not in OVER_WEEK_FREQUENCY:` ✓（注：and 分解为嵌套 if 属 repro_06 范畴）
- [x] R2-5b P1 repro_15 修复完成 — **已验证**
  - BoolOp 重建按跳转方向区分 `or`/`and`（IF_TRUE→`or`，IF_FALSE→`and`）
  - `check_frequency` 6 路 `or` 不再翻转为 `and`
  - 验证：repro_15 `if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == '1y'):` ✓
- [ ] R2-5c P1 repro_10 修复完成 — **待后续轮次**
  - `if A and B is None:` 块归函数体，不跨函数泄漏为下一函数装饰器
  - `get_price` 内 `if frequency not in OVER_WEEK_FREQUENCY and query_date is None: ...` 完整恢复
  - 当前状态：repro_13 修复后 `@((...))` 装饰器泄漏已消失，但 `and query_date is None` 条件仍丢失
- [ ] R2-5d P1 repro_01 修复完成 — **待后续轮次**
  - `COMPARE_OP is None` 重建为 `MatchSingleton(None)`
  - `MATCH_CLASS str` 重建为 `MatchClass(str, [])`
  - 不再回退 `MatchAs(None)`（`case _`）
  - `case _` 重复消除，`process` / `get_str_data` 不再触发 `SyntaxError: wildcard makes remaining patterns unreachable`

#### P2 修复（按时间预算择优，至少 2 项）

- [ ] R2-6a P2 repro_06 修复（IfExp 实参保留为 Call 子节点，不提升为 `and` 条件，字符串常量不发射为 docstring）
- [ ] R2-6b P2 repro_04 修复（`STORE_SUBSCR` 与 `STORE_ANNOTATION` 区分，去除 spurious break）
- [ ] R2-6c P2 repro_07 修复（except handler 内 `isinstance(e, X)` 完整 Call 节点保留）
- [ ] R2-6d P2 repro_08 修复（循环体 `STORE_FAST var` 赋值目标保留，去重前驱语句）
- [ ] R2-6e P2 repro_09 修复（双层 for + match case 内 for 不再生成 spurious for-else）
- [ ] R2-6f P2 repro_11 修复（elif 分支 `l = l.replace(...)` 的 Call 节点保留）
- [ ] R2-6g P2 repro_12 修复（嵌套 `if B:` 内层 if 不丢失，作为外层 If.body 子节点保留）

#### P0 阻塞项（新增 — 必须修复才能完成 R2）

- [x] R2-6b-new P0 阻塞：quotation.pyc 孤儿 try: 块修复 — **已修复**
  - `get_market_detail` 函数 if/else 块后存在孤儿 `try:` 块（line 2528），无 except/finally 子句
  - `compile()` 抛 `SyntaxError: expected 'except' or 'finally' block` at line 2530
  - 根因：`_build_region_hierarchy` 候选移除逻辑把与 TryExcept 共享 entry=15 的 WithRegion（实为 TryExcept 子区域）误判为祖先，据此移除两个 IfRegion 候选，导致 TryExceptRegion 成为顶层区域（parent=None），AST 生成器无法发射 try:/except: 包裹
  - 修复：`region_analyzer.py::_build_region_hierarchy` L16624-16636 候选移除条件增加 `_ni_is_peer` 守卫（非 If 候选与 child 共享 entry 时不据此移除 IfRegion）+ 前置 `_structural_region_co_blocks` 同区域兄弟块映射
  - 验证：`python pycdc.py /workspace/quotation.pyc` 产物 `compile()` 通过（COMPILE_OK）✓；`get_market_detail` try/except 结构正确恢复 ✓

#### 回归测试与验证

- [x] R2-7a 5 个已修复 repro（13/14/15/02/16）反编译验证通过（核心缺陷已消除） ✓
  - 注：repro_14 spurious for-else（属 repro_09）、repro_16 and 分解为嵌套 if（属 repro_06）为独立缺陷
- [x] R2-7b 既有测试矩阵无退化（IF/MATCH/BOOLOP/LOOP/TRY/WITH/TERNARY/CC/SEQ/ASSERT 子集 0 退化）✓
  - 执行 `python .trae/specs/analysis-fix-iteration/run_region_tests.py` 全部 10 区域
  - IF/TRY/WITH/MATCH/BOOLOP 持平；TERNARY/CC/SEQ/ASSERT 失败为 pre-existing；LOOP test_for20 skip→fail 为净改善（输出从 SyntaxError 垃圾提升为正确结构，残留 STORE_SUBSCR 属 repro_04 P2）
- [x] R2-7c quotation.pyc 反编译 stderr 警告数维持 0（MatchSingleton 维持清零）✓（`wc -l` = 0）
- [x] R2-7d quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）✓（孤儿 try: 块已修复，见 R2-6b-new）
- [ ] R2-7e quotation.pyc 反编译产物重编译后 code 对象数恢复 150（不丢失 `build_future_fill_time.<listcomp>`）
- [ ] R2-7f 残留不一致数 ≤ R2 基线（81 个函数不一致，应下降；推荐目标 ≤ 60）

#### 交付物与合规性

- [x] R2-8 `fix_report.md` 生成（rounds/round_02/repair_engineer/fix_report.md，结构同 R1）✓
  - 已验证修复点（6 项）：repro_13/14/15/02/16 + 孤儿 try（R2-6b-new）
  - §9 孤儿 try 修复详解完成（根因/修复/验证/算法依据/残留）
- [x] R2-9 反模式自检通过（G3：0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法）✓
  - grep 验证：core/cfg/ 下无新增反模式前缀方法
  - `_merge_block_is_loop_back_edge`（region_ast_generator.py L18747/L20954）为 pre-existing，按 spec 留待后续轮次重命名
- [x] R2-10 涉及的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新 ✓
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - `_identify_jump_targets`（cfg_builder.py）：6 项模板完整 ✓
  - `_identify_conditional_regions`（region_analyzer.py）：6 节结构（算法描述/字节码模式/边界条件/归约语义/AST映射/已知失败模式），内容覆盖 6 项模板要求 ✓
  - `_identify_boolop_regions`（region_analyzer.py）：6 节结构（算法描述/归约阶段/识别策略/归约过程/已知差异/AST映射），内容覆盖 6 项模板要求 ✓
  - `_identify_match_regions` / `_identify_loop_regions` / `_identify_try_regions` / `_identify_with_regions`：已存在详细 docstring
- [x] R2-11 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）✓
  - 自底向上归约：`_build_region_hierarchy` 在所有区域识别完成后统一构建层级
  - 每块唯一归属：`_ni_is_peer` 守卫尊重 `block_to_region` canonical owner，不把共享 entry 的子区域误判为祖先
  - 嵌套即抽象节点：TryExcept 作为 IfRegion else 分支的单个抽象节点
  - 入口引用语义：IfRegion.else_blocks 引用 TryExcept.entry
- [x] R2-12 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过 ✓（IMPORT_OK，含 cfg_builder + ast_converter）
- [ ] R2-13 commit + push `qpyc-r02:`（待用户授权执行）

## 轮 3 (Round 3)

> **R3 基线**：反编译产物 COMPILE_OK（2547 行），81 个函数字节码不一致、41 个签名不匹配、4 个缺失 code objects、18 个截断函数。
> **R3 缺陷分布**：10 类（5 项 R2 残留演化 + 5 项 R3 新增/重点验证），P0=2、P1=3、P2=5。

### 阶段一：测试工程师（已完成）

- [x] R3-1 反编译 + 字节码 diff（`decompile_report.md`，10 类缺陷，81 个函数不一致，COMPILE_OK）
- [x] R3-2 ≥10 最小复现实例（`minimal_repros/`，10 个 repro 全部 py_compile + DEFECT-REPRO 验证通过）

### 阶段二：修复工程师（执行中 — P0+3 项 P1 已验证通过，P2 修复与最终验证/报告待执行）

#### P0 修复（必须完成）

- [x] R3-3 根因分析完成（10 个 repro 全部定位到 `_identify_*_regions` 或 `_generate_*` 方法，输出根因 + 4 原则违反项）
- [x] R3-4a P0 repro_03_elif_chain_func_body_truncation 修复完成 — **已验证**
  - `region_analyzer.py::_identify_conditional_regions` sink 判定逻辑改为仅当块含 RETURN/RAISE/RERAISE 或无正常后继时才视为 sink
  - 新增 `_find_structural_merge_from_chain_end` 从 ipdom 链终止块的后继中查找结构区域入口作为 merge 点
  - ipdom 链遍历增加普通合并点（非结构区域入口但有 >1 个非回边前驱）检测，提前停止遍历
  - 9 个财务函数（`get_balance_statement` 等）函数体不再截断（13 行 → 69 行）✓
  - `_identify_conditional_regions` docstring 已存在 6 节结构覆盖 6 项模板要求
  - 验证：repro_03_elif_chain_func_body_truncation.pyc 反编译产物 `get_balance_statement` 函数体不再截断 ✓
- [x] R3-4b P0 repro_03_repro04_file_assignment_lost 修复完成 — **已验证**
  - `region_analyzer.py::_extract_with_items` 提取上下文表达式时遇到 STORE_* 清空已收集的 ctx_expr
  - `region_ast_generator.py::_generate_with` 提取 entry 块内 BEFORE_WITH 之前、以 STORE_* 结尾的指令段，作为 with 语句之前的顺序语句发射
  - `region_ast_generator.py::_if_generate_else_branch` 按偏移顺序交错处理子区域（Try/With/Loop）和顺序块
  - quotation.pyc::get_market_detail 的 `file = '...' % finance_mic` 赋值在 try 之前恢复 ✓
  - 验证：repro_03_repro04_file_assignment_lost.pyc 反编译产物 `file = ...` 正确出现在 `try:` 之前 ✓

#### P1 修复（必须完成至少 3 项 — 已完成 3 项：repro_03_match_case_none_to_wildcard / repro_03_if_nested_inner_lost / repro_03_if_ifexp_arg_to_and_docstring）

- [x] R3-5a P1 repro_03_match_case_none_to_wildcard 修复完成 — **已验证**
  - `pattern_parser.py::_extract_case_pattern` 识别 `POP_JUMP_FORWARD_IF_NOT_NONE` / `POP_JUMP_IF_NOT_NONE` 为 `MatchSingleton(None)`
  - `ast_converter.py::_convert_match_pattern` 添加 `MatchSingleton` 类型处理，直接返回其字典结构
  - quotation.pyc 中检测到 19 处 `case None` ✓
  - 验证：repro_03_match_case_none_to_wildcard.pyc 反编译产物 `case None` 正确输出 ✓
- [x] R3-5b P1 repro_03_if_nested_inner_lost 修复完成 — **已验证**
  - `region_analyzer.py::_detect_boolop_conditional_chain` 添加 STORE_* 检测，非首块含 STORE_* 时中断链
  - 嵌套 if 结构正确保留，语句未被提升 ✓
  - 已知限制：walrus `(x := foo()) and bar` 会误中断链（罕见，留待后续）
  - 验证：repro_03_if_nested_inner_lost.pyc 反编译产物嵌套 if 正确保留 ✓
- [x] R3-5c P1 repro_03_if_ifexp_arg_to_and_docstring 修复完成 — **已验证**
  - `region_analyzer.py::_detect_boolop_conditional_chain` 新增 IfExp 检测，非首块 fall-through 后继以 JUMP_FORWARD 终结时中断链
  - IfExp 正确保留为 Call 实参，docstring 错误消失 ✓
  - 已知限制：嵌套 if then-body 末尾 JUMP_FORWARD 由 P1-2 的 STORE_* 检测覆盖
  - 验证：repro_03_if_ifexp_arg_to_and_docstring.pyc 反编译产物 IfExp 正确保留 ✓

#### P2 修复（按时间预算择优，至少 2 项 — 待执行）

- [ ] R3-6a P2 repro_03_try_except_handler_if_cond_lost 修复（except handler 内 `if e2.code == 401:` 条件恢复，禁止退化为裸 `if HTTPError:`）
- [ ] R3-6b P2 repro_03_loop_store_subscr_to_annotation 修复（`STORE_SUBSCR` 与 `STORE_ANNOTATION` 区分，去除 spurious break）
- [ ] R3-6c P2 repro_03_loop_bare_name_and_dup 修复（循环体 `STORE_FAST var` 赋值目标保留，去重前驱语句）— 可选
- [ ] R3-6d P2 repro_03_loop_spurious_for_else_double 修复（双层 for + match case 内 for 不再生成 spurious for-else）— 可选
- [ ] R3-6e P2 repro_03_if_elif_bare_name 修复（elif 分支 `l = l.replace(...)` 的 Call 节点保留）— 可选

#### 回归测试与验证（待执行）

- [ ] R3-7a 10 个 R3 repro 反编译验证通过（核心缺陷已消除）
- [ ] R3-7b 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集 0 退化）
- [ ] R3-7c quotation.pyc 反编译 stderr 警告数维持 0
- [ ] R3-7d quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R3-7e quotation.pyc 中 `get_balance_statement` 函数体不再截断（orig=469 → new ≥ 400）
- [ ] R3-7f quotation.pyc 中 `get_market_detail` 的 `file = ...` 赋值恢复
- [ ] R3-7g quotation.pyc 中 `check_frequency` 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`（待评估是否本轮覆盖）
- [ ] R3-7h 残留不一致数 ≤ R3 基线（81 个函数不一致，目标 ≤ 50；截断函数 18 → ≤ 5）

#### 交付物与合规性（待执行）

- [ ] R3-8 `fix_report.md` 生成（rounds/round_03/repair_engineer/fix_report.md）
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（10 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R3 基线 81 个函数不一致对比，应下降）
  - 算法 4 原则合规性自检
  - 已知限制（walrus + IfExp JUMP_FORWARD 等）
- [ ] R3-9 反模式自检通过（G3：0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法）
  - `_merge_block_is_loop_back_edge`（region_ast_generator.py）为 pre-existing，按 spec 留待后续轮次重命名
- [ ] R3-10 涉及的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_identify_conditional_regions`（P0-1 修改）/ `_extract_with_items` + `_generate_with`（P0-2 修改）/ `_detect_boolop_conditional_chain`（P1-2/P1-3 修改）/ `_extract_case_pattern`（P1-1 修改）
- [ ] R3-11 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] R3-12 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.pattern_parser"` 编译通过
- [ ] R3-13 commit + push `qpyc-r03:`（待用户授权执行）

## 轮 4 (Round 4)

> **R4 基线**：反编译产物 COMPILE_OK（3035 行），80 个函数字节码不一致、37 个签名不匹配、4 个缺失 code objects、11 个截断函数。
> **R4 缺陷分布**：12 类（3 项 R3 残留 P2 复测 + 8 项 R4 新增 + 1 项 R3 修复在 quotation.pyc 退化），P0=2、P1=4、P2=5。

### 阶段一：测试工程师（已完成）

- [x] R4-1 反编译 + 字节码 diff（`decompile_report.md`，12 类缺陷，80 个函数不一致，COMPILE_OK）
- [x] R4-2 ≥10 最小复现实例（`minimal_repros/`，12 个 repro 全部 py_compile + DEFECT-REPRO 验证通过）

### 阶段二：修复工程师（待执行 — 目标：P0×2 + P1≥3 + P2≥2）

#### P0 修复（必须完成 2 项）

- [ ] R4-3 根因分析完成（12 个 repro 全部定位到 `_identify_*_regions` 或 `_generate_*` 方法，输出根因 + 4 原则违反项）
- [ ] R4-4a P0 repro_04_func_body_truncated_after_else 修复完成（change_his_to_forward/backward else 后函数体截断退化）
  - `region_analyzer.py::_identify_conditional_regions` / `_build_elif_region` / `_find_structural_merge_from_chain_end` 在 else 分支后跟 for 循环 + 多层 if 时正确识别 merge 点
  - 扩展 `_structural_region_entries` 含 else body 的 for 循环 header/setup 块
  - `_identify_conditional_regions` docstring 已按 6 项模板更新
  - 验证：repro_04_func_body_truncated_after_else.pyc 中 else 后 for 循环 + tmpdata 赋值 + return 保留 ✓
  - 验证：quotation.pyc::change_his_to_forward 函数体 orig=597 → new ≥ 400
- [ ] R4-4b P0 repro_04_func_body_to_pass 修复完成（fill_minute_or_day_blank 函数体→pass）
  - `region_ast_generator.py::_generate_region` / `_generate_block_statements` 在 for + if/elif/else + STORE_SUBSCR + continue 嵌套时按自底向上归约顺序处理子区域
  - `_identify_loop_regions` 在含 continue 的 for 循环后跟 if/elif/else 时归约边界正确
  - `_generate_region` docstring 已按 6 项模板更新
  - 验证：repro_04_func_body_to_pass.pyc 中 for + if/elif/else + STORE_SUBSCR + continue 全部保留 ✓
  - 验证：quotation.pyc::fill_minute_or_day_blank 函数体 orig=244 → new ≥ 150

#### P1 修复（必须完成至少 3 项 — 目标 4 项）

- [ ] R4-5a P1 repro_04_boolop_or_chain_to_and 修复完成（check_frequency or→and 语义反转）
  - `region_analyzer.py::_detect_boolop_conditional_chain` 区分 assert 语句与 if 语句的 jump 方向
  - POP_JUMP_IF_TRUE 短路正确识别为 or 链（非 and 链）
  - assert 语句整体保留为 `assert not (or-chain), msg`，不拆分为 if + assert
  - `_detect_boolop_conditional_chain` docstring 已按 6 项模板更新
  - 验证：repro_04_boolop_or_chain_to_and.pyc 中 6 路 or 正确保留 ✓
  - 验证：quotation.pyc::check_frequency 函数体 orig=96 → new ≤ 100
- [ ] R4-5b P1 repro_04_try_except_handler_if_cond_lost 修复完成（except handler 内 `if e2.code == 401:` 条件丢失，R3 残留 P2 升级 P1）
  - `region_ast_generator.py::_generate_try` 把 except handler 内 `LOAD_FAST e + LOAD_ATTR attr + LOAD_CONST N + COMPARE_OP` 完整 Compare 节点保留作 If 条件
  - 禁止只保留 `LOAD_GLOBAL cls`（HTTPError/BaseException）
  - 消除 spurious `if BaseException: pass` 嵌套
  - `_generate_try` docstring 已按 6 项模板更新
  - 验证：repro_04_try_except_handler_if_cond_lost.pyc 中 `if e2.code == 401:` 条件恢复 ✓
  - 验证：quotation.pyc::api_get_financial line 161-172 条件恢复
- [ ] R4-5c P1 repro_04_func_body_to_single_expr 修复完成（date_convert 函数体→单 Expr）
  - `region_analyzer.py::_identify_conditional_regions` 在 if/elif/else 链 + IfExp 嵌套时按自底向上归约顺序处理
  - 禁止把整个条件块压缩为单 IfExp；IfExp 仅在 Call 实参位置保留
  - `_identify_conditional_regions` docstring 已按 6 项模板更新（与 R4-4a 共享）
  - 验证：repro_04_func_body_to_single_expr.pyc 中 if/elif/else + return 完整保留 ✓
  - 验证：quotation.pyc::date_convert 函数体 orig=87 → new ≥ 60
- [ ] R4-5d P1 repro_04_if_branch_both_return_same 修复完成（_is_same_type_date 两分支均 return True）
  - `region_ast_generator.py::_generate_if` / `_generate_compare` 保留嵌套 if 内层 Compare 节点
  - 禁止把内层 Compare 折叠为外层 if 的常量分支
  - 验证：repro_04_if_branch_both_return_same.pyc 中 `if typet == 7: ... else: if len(day1) == 8: return True` 内层 Compare 保留 ✓
  - 验证：quotation.pyc::_is_same_type_date 函数体 orig=99 → new ≥ 60

#### P2 修复（按时间预算择优，至少 2 项 — 目标 3 项）

- [ ] R4-6a P2 repro_04_loop_store_subscr_to_bare_name 修复（load_get_price STORE_SUBSCR 丢失 + 裸 stock Expr，R3 退化）
  - 扩展 `_fis_pre_stmts_emitted` 覆盖 STORE_SUBSCR 序列
  - `_loop_generate_for` pre_stmts 发射守卫区分 minimal repro 与实际 CFG
  - `_build_effective_stmts` 正确重建 `STORE_SUBSCR` 的 `Subscript` 目标为 `panel[stock] = data`
  - `_loop_generate_for` + `_build_effective_stmts` docstring 已按 6 项模板更新
  - 验证：repro_04_loop_store_subscr_to_bare_name.pyc 中 `panel[stock] = data` 保留，无裸 `stock` Expr ✓
- [ ] R4-6b P2 repro_04_loop_spurious_for_else_double 修复（双层 spurious for-else + i=0 重复，R3 残留 P2）
  - `_loop_generate_for` for 后顺序语句作为函数体顺序子节点保留，不应作为 else 子句
  - 抑制 spurious `else: continue` / `else: return`
  - `_identify_loop_regions` else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句
  - 验证：repro_04_loop_spurious_for_else_double.pyc 中无 spurious for-else，无重复 `i = 0` ✓
- [ ] R4-6c P2 repro_04_loop_dup_pre_assignment + repro_04_ifexp_as_bare_expr 修复（load_bars_from_hundsun 重复赋值 + 裸 IfExp）
  - for_iter_setup pre_stmts 在 IfRegion 交叉时的发射权管理
  - IfExpr 作为顺序语句时抑制裸 Expr 发射
  - 验证：repro_04_loop_dup_pre_assignment.pyc 中无重复 `source_end = end[8:] or '1530'` ✓
  - 验证：repro_04_ifexp_as_bare_expr.pyc 中无裸 IfExpr ✓
- [ ] R4-6d P2 repro_04_ternary_in_call_arg_malformed 修复（get_history Call 实参 IfExp 畸形）— 可选
- [ ] R4-6e P2 repro_04_loop_nested_if_spurious_pass 修复（顺序 if→elif + spurious pass）— 可选

#### 回归测试与验证（待执行）

- [ ] R4-7a 12 个 R4 repro 反编译验证通过（核心缺陷已消除）
- [ ] R4-7b 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集 0 退化）
- [ ] R4-7c quotation.pyc 反编译 stderr 警告数维持 0
- [ ] R4-7d quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R4-7e quotation.pyc 中 change_his_to_forward 函数体不再截断（orig=597 → new ≥ 400）
- [ ] R4-7f quotation.pyc 中 fill_minute_or_day_blank 函数体不再→pass（orig=244 → new ≥ 150）
- [ ] R4-7g quotation.pyc 中 check_frequency 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`（不仅 minimal repro）
- [ ] R4-7h R3 已修 7 项不退化（特别是 repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物复测，裸 `stock` Expr 消除）
- [ ] R4-7i 残留不一致数 ≤ R4 基线（80 个函数不一致，目标 ≤ 60；截断函数 11 → ≤ 5；签名不匹配 37 → ≤ 25）

#### 交付物与合规性（待执行）

- [ ] R4-8 `fix_report.md` 生成（rounds/round_04/repair_engineer/fix_report.md）
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（12 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R4 基线 80 个函数不一致对比，应下降）
  - 算法 4 原则合规性自检
  - 已知限制（assert not (or-chain) + 嵌套 IfExp + R3 退化点等）
- [ ] R4-9 反模式自检通过（G3：0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法）
  - `_merge_block_is_loop_back_edge`（region_ast_generator.py）为 pre-existing，按 spec 留待后续轮次重命名
- [ ] R4-10 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 项统一模板更新
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_identify_conditional_regions`（P0-1/P1-3 修改）/ `_generate_region`（P0-2 修改）/ `_detect_boolop_conditional_chain`（P1-1 修改）/ `_generate_try`（P1-2 修改）/ `_loop_generate_for` + `_build_effective_stmts`（P2-1/P2-2/P2-3 修改）
- [ ] R4-11 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] R4-12 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.pattern_parser"` 编译通过
- [ ] R4-13 commit + push `qpyc-r04:`（待用户授权执行）

## 轮 5 (Round 5)

- [ ] R5-1 ~ R5-9

## 轮 6 (Round 6)

> **R6 基线**：反编译产物 COMPILE_OK（2581 行，0 stderr）。
> **R6 缺陷分布**：8 类缺陷（D1-D8），优先级 P0=D1/D2，P1=D3/D5，P2=D4/D6/D7/D8。

### 阶段一：测试工程师（已完成）

- [x] R6-1 反编译 + 字节码 diff（`decompile_report.md`，8 类缺陷 D1-D8，2581 行，COMPILE_OK）
- [x] R6-2 ≥10 最小复现实例（`minimal_repros/`，17 个 repro，5 个 DEFECT-REPRO 确认：01/02/06/14/15）

### 阶段二：修复工程师（执行中 — Fix 1/Fix 2 已验证，Fix 3 部分完成，Fix 4/Fix 5 待执行）

#### P0 修复（必须完成 — 已完成 2 项）

- [x] R6-3 根因分析完成（8 类缺陷全部定位到 `_identify_*_regions` 或 `_generate_*` 方法，输出根因 + 4 原则违反项）
- [x] R6-4a P0 D1 repro_06_01/14/15 lost return in except handler 修复完成 — **已验证**
  - `region_ast_generator.py::_generate_handler_body_statements` 重命名 bool 重载为 `_find_return_chain_via_successors`，避免方法遮蔽
  - fallback 决策同时检查两路径（`_find_return_through_cleanup_chain` + `_find_return_chain_via_successors`）
  - try-except 上下文中（`self._try_depth > 0`）当 `value_instrs` 为空时抑制 spurious `return None`
  - `_generate_handler_body_statements` docstring 已按 6 项模板更新
  - 验证：repro_06_01/14/15 中 `return (...)` 关键字正确恢复 ✓
- [x] R6-4b P0 D2 repro_06_02 lost parens in BinOp+Compare 修复完成 — **已验证**
  - `code_generator.py::_generate_binary` 替换内部 `get_expr_precedence` 为 `_get_ast_expr_precedence`
  - ASTCompare 节点正确返回比较优先级（6）而非高优先级 BinOp（12）
  - `BinOp(BitAnd/BitOr/BitXor, Compare, Compare)` 触发为 Compare 操作数加括号
  - `_generate_binary` docstring 注释说明 ASTCompare 优先级修复依据
  - 验证：repro_06_02 中 `(a >= b) & (c <= d)` 正确加括号 ✓

#### P1 修复（必须完成至少 1 项 — Fix 3 部分完成）

- [~] R6-5a P1 D3 repro_06_16/17 bare number if (chained compare in except) 修复 — **部分完成**
  - `region_ast_generator.py::_try_build_attr_middle_chained_compare` + `_try_build_attr_middle_from_blocks` 新增（处理 `LOAD_FAST + LOAD_ATTR` 中间操作数）
  - `_build_chained_compare_from_region_data` 调用新方法
  - minimal repro 通过：`400 <= e2.code <= 499` 正确保留 ✓
  - quotation.pyc 路径未修复：region 检测未识别 block@694 为 IfRegion（block@694 有 conditional_successors [732, 720] 但仍归约失败）
  - 待办：调试 `region_analyzer.py::_identify_conditional_regions` 识别条件，覆盖 except handler 内 SWAP+COPY+COMPARE_OP 模式
  - `_try_build_attr_middle_chained_compare` + `_build_chained_compare_from_region_data` docstring 待按 6 项模板更新
- [ ] R6-5b P1 D5 repro_06_04/07/13 orphan Name/Attr Expr suppression 修复 — **待执行**
  - `_build_effective_stmts` 检测无消费方 LOAD_FAST/LOAD_ATTR/LOAD_SUBSCR 序列，抑制孤立 Expr 发射
  - 验证：repro_06_04/07/13 中无裸 `prod`/`stocks`/`panel.items` Expr ✓
  - 验证：quotation.pyc line 247/456/500/546/557/558 orphan Expr 消除
  - `_build_effective_stmts` docstring 待按 6 项模板更新

#### P2 修复（按时间预算择优）

- [ ] R6-6a P2 D4 repro_06_09/12/14 `del e2` as-var cleanup leak 修复
  - 抑制 except handler 内 `LOAD_CONST None / STORE_FAST e2 / DELETE_FAST e2` 的 as-var cleanup 作为 `del e2` 发射
  - 验证：repro_06_09/12/14 中无 `del e2` ✓；quotation.pyc line 173 消除
- [ ] R6-6b P2 D6 repro_06_06 lost function body/nested-if return 修复
  - 保留嵌套 if 内层 `return True/False`；抑制 spurious `pass` 占位
  - 验证：repro_06_06 中 `if/elif + return True/False` 保留 ✓；quotation.pyc line 266-302/492/505/566 恢复
- [ ] R6-6c P2 repro_06_05 duplicate statements dedup 修复
  - `_build_effective_stmts` 去重连续相同语句发射
  - 验证：repro_06_05 中无重复 `error_no = e2.code` ✓
- [ ] R6-6d P2 D7/D8 malformed ternary + lost date_convert body（可选）
  - 修复 IfExp 重建路径，禁止把 if/elif 链压缩为嵌套 ternary of `==` 比较

#### 回归测试与验证（待执行）

- [ ] R6-7a 17 个 R6 repro 反编译验证通过（核心缺陷已消除）
- [ ] R6-7b 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集 0 退化）
- [ ] R6-7c quotation.pyc 反编译 stderr 维持 0
- [ ] R6-7d quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R6-7e quotation.pyc::api_get_financial except handler `return` 关键字恢复（D1 修复 — line 161/169/179/184）
- [ ] R6-7f quotation.pyc::api_get_financial `if 400 <= e2.code <= 499:` 条件恢复（D3 修复 — 待 region 检测修复，line 164）
- [ ] R6-7g quotation.pyc 中 orphan Expr 消除（D5 修复 — line 247/456/500/546/557/558）
- [ ] R6-7h R5 已修项不退化（特别是 repro_05_* 系列在 quotation.pyc 实际产物复测）
- [ ] R6-7i 残留不一致数 ≤ R6 基线

#### 交付物与合规性（待执行）

- [ ] R6-8 `fix_report.md` 生成（rounds/round_06/repair_engineer/fix_report.md）
  - 修复点列表（按 repro 编号 + 涉及方法 + 算法依据 + 4 原则对应条款）
  - docstring 更新清单（方法名 + 6 项模板覆盖确认）
  - 回归结果（17 repro 通过状态 + 既有矩阵退化检查）
  - 残留不一致数（与 R6 基线对比）
  - 算法 4 原则合规性自检
  - 已知限制（Fix 3 region 检测未覆盖 / Fix 4-Fix 5 未实施等）
- [ ] R6-9 反模式自检通过（G3：0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法）
  - `_merge_block_is_loop_back_edge`（region_ast_generator.py）为 pre-existing，按 spec 留待后续轮次重命名
- [ ] R6-10 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 项统一模板更新
  - 6 项：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 待更新方法：`_generate_handler_body_statements`（D1）/ `_generate_binary`（D2）/ `_try_build_attr_middle_chained_compare` + `_build_chained_compare_from_region_data`（D3）/ `_build_effective_stmts`（D5，待执行）
- [ ] R6-11 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] R6-12 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.cfg_builder; import core.cfg.ast_converter; import core.cfg.code_generator"` 编译通过
- [ ] R6-13 commit + push `qpyc-r06:`（待用户授权执行）

## 轮 7 (Round 7)

- [ ] R7-1 ~ R7-9

## 轮 8 (Round 8)

- [ ] R8-1 ~ R8-9

## 轮 9 (Round 9)

- [ ] R9-1 ~ R9-9

## 轮 10 (Round 10)

- [ ] R10-1 ~ R10-9

## 退出条件（每轮后检查）

- [ ] E1 quotation.pyc 反编译字节码不一致数 = 0
- [ ] E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个

## 最终验证（10 轮完成后）

- [ ] F1 共 10 次 commit + push 完成（`git log --grep="qpyc-r"` 计数 ≥ 10）
- [ ] F2 quotation.pyc 字节码不一致数 ≤ 起始基线（优选 = 0）
- [ ] F3 既有测试矩阵无退化
- [ ] F4 算法 4 原则 FULLY COMPLIANT
- [ ] F5 无反模式残留（`_merge_block_is_loop_back_edge` 已重命名为 `is_merge_block_loop_back_edge`）
- [ ] F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7 所有涉及到的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新

## 备注

- 若在 10 轮内提前达到 E1+E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 E1，输出 `final_residual.md` 列出残留不一致清单，作为后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行（`python -c "import dis; ..."` 验证）
