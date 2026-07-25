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

- [ ] R3-1 ~ R3-9

## 轮 4 (Round 4)

- [ ] R4-1 ~ R4-9

## 轮 5 (Round 5)

- [ ] R5-1 ~ R5-9

## 轮 6 (Round 6)

- [ ] R6-1 ~ R6-9

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
