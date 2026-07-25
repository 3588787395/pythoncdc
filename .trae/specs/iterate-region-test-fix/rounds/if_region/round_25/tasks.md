# Round 25 Tasks — IF 区域 R25-A/B/C/D 簇修复

## 目标
- 修复测试工程师发现的 13 个错误中的 5+ 个（最少目标）
- IF 区域失败数 ≤ 25（基线 17 旧 + 13 新 = 30，目标 -5）
- ternary 区域 0 回归（基线 0 failed / 506 passed / 36 skipped）
- 所有修复依区域归约算法 4 原则

## 基线
- if_region: 17 failed / 800 passed / 10 skipped
- ternary: 0 failed / 506 passed / 36 skipped
- R25 新测试: 13 failed / 20 passed / 4 skipped

## 错误聚类（来自 test_findings.md）
| 簇 | 描述 | 涉及 Finding | 数量 | 优先级 |
|---|---|---|---|---|
| R25-A | if-elif-else 头坍塌为三元（await/f-string/ternary+boolop 在 elif 上下文） | R25-01, 03, 04, 13 | 4 | P0 |
| R25-B | 嵌套 for-else / try-else-finally / with / global+del 的 else/cleanup 子句归属错位 | R25-02, 05, 07, 09, 11, 12 | 6 | P0 |
| R25-C | 多目标赋值 / tuple return 中表达式归约失败 | R25-06, 10 | 2 | P1 |
| R25-D | lambda IIFE 在 elif 条件中递归反编译 body 退化 | R25-08 | 1 | P1 |

## 当前进度（已完成 6 个修复，目标 5+ 已达成 ✅）
- [x] R25-C-01/R25-06: multi-target 赋值 ternary 后 return 丢失 ✓
  - 修复点: `core/cfg/region_ast_generator.py` 多目标赋值处理逻辑添加 trailing 语句生成
  - 算法原则: 原则 2（每块唯一归属）+ 原则 4（父引用子入口）
- [x] R25-B-12: try-finally cleanup_blocks 互换 ✓
  - 修复点: `core/cfg/region_analyzer.py` `_check_elif_chain` 添加 try/with handler block 过滤，防止跨区域 cleanup 块污染
  - 算法原则: 原则 2（每块唯一归属）
- [x] R25-B-09: try-except-else-finally cleanup 丢失 ✓
  - 修复点: `core/cfg/region_analyzer.py` cleanup_blocks 收集改用 exception table chain 遍历（_chain_target_set + _chain_entry_ids），正确隔离不同 TryExceptRegion 的 cleanup 块
  - 算法原则: 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）
- [x] R25-B-11: global + del 在 elif body 时 else 分支结构丢失 ✓
  - 修复点: `core/cfg/region_ast_generator.py` trailing return 优化改为在 if/elif body 含隐式 return None 时保留 else 分支结构
  - 算法原则: 原则 4（父引用子入口）
- [x] R25-D-08: lambda IIFE 递归反编译 body 退化 ✓
  - 修复点: `core/cfg/region_ast_generator.py` `_convert_lambda_function_objects` 列式子节点遍历扩展至 body/orelse/cases/items/finalbody
  - 算法原则: 原则 1（自底向上归约）
- [x] R25-C-10: tuple return + comprehension 丢失 ✓
  - 修复点: `core/cfg/comprehension_generator.py` `try_generate_comprehension_assign` 在 pre_comp_instrs 末尾不是语句终止符（STORE/POP_TOP/IMPORT）或 post-wrapper 含 BUILD_TUPLE/BINARY_OP 时返回 None，让标准 expr_reconstructor.reconstruct 处理整个块
  - 算法原则: 原则 3（嵌套即抽象节点）— comprehension 作为 Tuple.elts 子节点

## Tasks

### Phase 1: 基线确认与准备
- [x] Task 1.0: 基线确认 — R25 测试套件 13 failed / 20 passed / 4 skipped
- [x] Task 1.1: if_region 全量回归基线 17 failed / 800 passed / 10 skipped
- [x] Task 1.2: ternary 全量回归基线 0 failed / 506 passed / 36 skipped

### Phase 2: P0 修复 — R25-B 簇（try/with/for-else cleanup 归属错位）
- [x] Task 2.1: 修复 R25-12 (try-finally cleanup_blocks 互换) ✅
  - 根因: 两个 TryExceptRegion 的 cleanup_blocks 字段互换，第一个 try 的 cleanup 块被第二个 try 处理
  - 修复点: `core/cfg/region_analyzer.py` `_check_elif_chain` 添加 try/with handler block 过滤（_elif_try_handler_blocks + _elif_with_handler_blocks）
  - 算法原则: 原则 2（每块唯一归属）
  - 验证: `tests/exhaustive/if_region/test_r25_try_finally_raise_each_branch.py` 通过
- [x] Task 2.2: 修复 R25-09 (try-except-else-finally cleanup 丢失) ✅
  - 根因: elif 分支的 finally_blocks 被 IfRegion.elif_bodies 与 TryExceptRegion.finally_blocks 争抢
  - 修复点: `core/cfg/region_analyzer.py` cleanup_blocks 收集改用 exception table chain 遍历（_chain_target_set + _chain_entry_ids），替换原 _valid_handler_targets
  - 算法原则: 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）
  - 验证: `tests/exhaustive/if_region/test_r25_try_else_finally_each_branch.py` 通过
- [x] Task 2.3: 评估 R25-B 其余（R25-02/05/07/11）— R25-11 已修，其余标记已知限制 ✅
  - [x] R25-11: global + del — 已修（trailing return 优化）
  - [ ] R25-02: for-else + continue — 标记为已知限制（涉及 LoopRegion else 块与 IfRegion.elif_bodies 争抢，需重构 _collect_branch_blocks 把 ForLoop 作为整体子节点）
  - [ ] R25-05: for + continue + try — 标记为已知限制（continue JUMP_BACKWARD 块归属冲突）
  - [ ] R25-07: nested with + multi context — 标记为已知限制（WithRegion 多 context 与嵌套 with 共享 cleanup 块链）

### Phase 3: P0 修复 — R25-A 簇（if-elif-else 头坍塌为三元）
- [ ] Task 3.1: 修复 R25-01 (await call arg in elif) — 未完成，标记为已知限制
  - 根因: `_collect_await_predecessor_chain` 仅收集单组 setup+poll；多 await 时剩余 await 块被当作 BoolOpRegion 抢占 if 头块
  - 修复点（待 R26+）: `core/cfg/region_analyzer.py: _collect_await_predecessor_chain` (4425) 沿前驱链完整收集所有 await setup+poll 对
  - 算法原则: 原则 1（自底向上归约）+ 原则 4（父引用子入口）
  - 状态: 在算法框架内未找到无退化修复方案，标记为已知限制
- [x] Task 3.2: 评估 R25-A 其余（R25-03/04/13）— 全部标记为已知限制
  - [ ] R25-03: f-string + ternary + walrus — 已知限制（IfExp 在 f-string FORMAT_VALUE 上下文抢占 if 头）
  - [ ] R25-04: await in subscript — 已知限制（与 R25-01 同源 C5，await 位置在 subscript）
  - [ ] R25-13: ternary + boolop in elif cond — 已知限制（BoolOp op_chain 修剪 ternary value 块导致运算符优先级错误）

### Phase 4: P1 修复 — R25-C + R25-D 簇
- [x] Task 4.1: 修复 R25-10 (tuple return + comprehension 丢失) ✅
  - 根因: BUILD_TUPLE 2/3 元素块（含 comprehension 的 MAKE_FUNCTION + GET_ITER + CALL）被作为独立 BASIC 块处理
  - 修复点: `core/cfg/comprehension_generator.py` `try_generate_comprehension_assign` 在 pre_comp_instrs 末尾非语句终止符或 post-wrapper 含表达式构建指令时返回 None
  - 算法原则: 原则 3（嵌套即抽象节点）— comprehension 应作为 return value 的 Tuple.elts 子节点
  - 验证: `tests/exhaustive/if_region/test_r25_tuple_return_comprehension.py` 通过
- [x] Task 4.2: 修复 R25-08 (lambda IIFE 退化) ✅
  - 根因: lambda code object 的递归反编译未走完整的 region_analyzer 流程，body 退化为 `*args, **kwargs: None`
  - 修复点: `core/cfg/region_ast_generator.py` `_convert_lambda_function_objects` 列式子节点遍历扩展至 body/orelse/cases/items/finalbody
  - 算法原则: 原则 1（自底向上归约）
  - 验证: `tests/exhaustive/if_region/test_r25_lambda_iife_in_elif_cond.py` 通过

### Phase 5: 全量回归与算法合规性自检
- [x] Task 5.1: 全量 IF 区域回归 — 失败数 24（基线 30，-6，≤25 目标达成 ✅）
- [x] Task 5.2: 全量 ternary 区域回归 — 0 failed（无退化 ✅）
- [x] Task 5.3: 算法合规性自检（4 原则）
  - [x] 自底向上归约
  - [x] 每块唯一归属
  - [x] 嵌套即抽象节点
  - [x] 父引用子入口
  - [x] 无跨区域启发式特例 / 后处理补丁 / 展平嵌套 / 硬编码深度上限
- [x] Task 5.4: 清理调试文件（不创建根级 _debug_*.py）

### Phase 6: 修复报告与 checklist 更新
- [ ] Task 6.1: 写 fix_report.md（含每个 bug 详细修复说明 + 算法 4 原则合规论证 + 全量回归结果 + 已知限制记录）— 待 Spec Mode 退出后由实现代理完成
- [x] Task 6.2: 更新 checklist.md（勾选完成的验证项）✅
- [x] Task 6.3: 更新父级 tasks.md（添加 Task 1.25 IF round_25 条目）✅

## 修复优先级（依 test_findings.md 建议）
1. **P0 - 先修 R25-B**（覆盖 6 个测试）: 嵌套 for-else / try-else-finally / with 的 else/cleanup 子句在三分支内归属错位。`_collect_branch_blocks` 应把 LoopRegion/TryExceptRegion/WithRegion 作为整体子节点，不沿 fallthrough 拆解其内部 blocks
2. **P0 - 再修 R25-A**（覆盖 4 个测试）: if-elif-else 头坍塌为三元。`_collect_await_predecessor_chain` 应沿前驱链完整收集所有 await setup+poll 对；f-string/ternary 在 body 值上下文时不应抢占 if 头
3. **P1 - 修 R25-C + R25-D**（覆盖 3 个测试）: multi-target 赋值 + ternary 在 elif body 的 return 丢失；lambda IIFE 在 elif 递归反编译退化

## 实际修复结果汇总
- **已修复 6 个**（超出 5+ 目标）: R25-06, R25-09, R25-10, R25-11, R25-12, R25-08
- **已知限制 7 个**（待 R26+ 处理）: R25-01, R25-02, R25-03, R25-04, R25-05, R25-07, R25-13
- **if_region 失败数**: 30 → 24（-6，≤25 目标达成 ✅）
- **ternary 回归**: 0 failed（无退化 ✅）

## 严格约束
- 所有命令执行不得超过 300 秒
- 修复依区域归约算法 4 原则
- 不要修改任何测试文件
- 不要 git commit
- 不要创建根级 debug 文件（_debug_*.py）
- 无法在算法框架内修复的错误标记为「已知限制」

## 关键参考
- 区域归约算法 4 原则: `/workspace/.trae/specs/iterate-region-test-fix/spec.md`
- 上一轮 R24 修复报告: `/workspace/.trae/specs/iterate-region-test-fix/rounds/if_region/round_24/fix_report.md`
- region_analyzer.py 中相关方法的 docstring（`_collect_branch_blocks` / `_collect_await_predecessor_chain` / `_identify_with_regions`）
- 错误清单: `/workspace/.trae/specs/iterate-region-test-fix/rounds/if_region/round_25/test_findings.md`

# Task Dependencies
- [Task 2.1] (R25-12 cleanup_blocks 互换) 是 [Task 2.2] (R25-09 try-else-finally) 的前置 — 同根因（cleanup 块归属），先修简单场景 ✅ 已按序完成
- [Task 3.1] (R25-01 await) 与 [Task 2.x] (R25-B) 可并行 — 不同根因簇（R25-01 标记为已知限制）
- [Task 4.1] (R25-10 tuple) 与 [Task 4.2] (R25-08 lambda) 可并行 — 不同根因簇 ✅ 已并行完成
- [Task 5.x] (回归) 依赖所有修复 Task 完成 ✅ 已完成
- [Task 6.x] (报告) 依赖回归 Task 完成 — checklist 已更新，fix_report 待 Spec Mode 退出后写
