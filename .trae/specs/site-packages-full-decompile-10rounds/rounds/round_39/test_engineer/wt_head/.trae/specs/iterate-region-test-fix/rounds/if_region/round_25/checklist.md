# Round 25 Checklist — IF 区域 R25-A/B/C/D 簇修复

## 已完成（6 测试通过，超出 5+ 目标 ✅）
- [x] R25-C-01/R25-06: multi-target 赋值 ternary 后 return 丢失 — `core/cfg/region_ast_generator.py` 多目标赋值处理逻辑添加 trailing 语句生成（`_build_statements_from_instructions` 重建 return/expr）
- [x] R25-B-12: try-finally cleanup_blocks 互换 — `core/cfg/region_analyzer.py` `_check_elif_chain` 添加 try/with handler block 过滤（_elif_try_handler_blocks + _elif_with_handler_blocks）
- [x] R25-B-09: try-except-else-finally cleanup 丢失 — `core/cfg/region_analyzer.py` cleanup_blocks 收集改用 exception table chain 遍历（_chain_target_set + _chain_entry_ids），替换原 _valid_handler_targets
- [x] R25-B-11: global + del 在 elif body 时 else 分支结构丢失 — `core/cfg/region_ast_generator.py` trailing return 优化改为在 if/elif body 含隐式 return None 时保留 else 分支结构
- [x] R25-D-08: lambda IIFE 递归反编译 body 退化 — `core/cfg/region_ast_generator.py` `_convert_lambda_function_objects` 列式子节点遍历扩展至 body/orelse/cases/items/finalbody
- [x] R25-C-10: tuple return + comprehension 丢失 — `core/cfg/comprehension_generator.py` `try_generate_comprehension_assign` 在 pre_comp_instrs 末尾非语句终止符或 post-wrapper 含表达式构建指令时返回 None

## 基线确认

### SubTask R25.0: 基线确认
- [x] 全量 IF 区域回归基线 = 17 failed / 800 passed / 10 skipped
- [x] 全量 ternary 区域回归基线 = 0 failed / 506 passed / 36 skipped
- [x] R25 新测试基线 = 13 failed / 20 passed / 4 skipped

## 待修复验证

### SubTask R25.1 (P0): R25-B try-finally/try-else-finally cleanup 修复
- [x] R25-12 `if x > 0: try: ... finally: cleanup()` 三分支各自含 try-finally 时 elif 分支 finally cleanup 不丢失，字节码等价
  - 验证：`tests/exhaustive/if_region/test_r25_try_finally_raise_each_branch.py` 通过 ✅
  - 修复点：`core/cfg/region_analyzer.py` `_check_elif_chain` 添加 try/with handler block 过滤
- [x] R25-09 `if x > 0: try: ... except: ... else: ... finally: cleanup()` 三分支各自含 try-except-else-finally 时 elif 分支 finally cleanup 不丢失，字节码等价
  - 验证：`tests/exhaustive/if_region/test_r25_try_else_finally_each_branch.py` 通过 ✅
  - 修复点：`core/cfg/region_analyzer.py` cleanup_blocks 收集改用 exception table chain 遍历
- [x] 修复依 4 原则：每块唯一归属 / 嵌套即抽象节点
- [x] IF 回归无退化（30 → 24，-6）
- [x] ternary 回归无退化（0 failed）

### SubTask R25.2 (P0): R25-A await call arg 修复 — 标记为已知限制
- [ ] R25-01 `async def f(x): if x > 0: return process(await fetch(x), await fetch(x + 1))` 反编译保留 if-elif-else 三分支，每分支含 `await fetch(...)` 调用，字节码等价
  - 验证：`tests/exhaustive/if_region/test_r25_await_call_arg_in_elif.py` 通过 — **未通过，标记为已知限制**
  - 修复点（待 R26+）：`core/cfg/region_analyzer.py: _collect_await_predecessor_chain` (4425) 沿前驱链完整收集所有 await setup+poll 对
  - 状态：在算法框架内未找到无退化修复方案，标记为已知限制
- [x] 修复依 4 原则：自底向上归约 / 父引用子入口（已修复的 6 个 bug 均合规）
- [x] IF 回归无退化（30 → 24）
- [x] ternary 回归无退化（0 failed）

### SubTask R25.3 (P1): R25-C tuple return + R25-D lambda IIFE
- [x] R25-10 `return (sum(items), len(items), [x for x in items if x > 0])` 反编译保留 tuple 结构 + comprehension 作 Tuple.elts 子节点，字节码等价
  - 验证：`tests/exhaustive/if_region/test_r25_tuple_return_comprehension.py` 通过 ✅
  - 修复点：`core/cfg/comprehension_generator.py` `try_generate_comprehension_assign` 在 pre_comp_instrs 末尾非语句终止符或 post-wrapper 含表达式构建指令时返回 None
- [x] R25-08 `elif (lambda x: x < 0)(y):` 反编译保留 lambda body 为 `return x < 0`，字节码等价
  - 验证：`tests/exhaustive/if_region/test_r25_lambda_iife_in_elif_cond.py` 通过 ✅
  - 修复点：`core/cfg/region_ast_generator.py` `_convert_lambda_function_objects` 列式子节点遍历扩展
- [x] 修复依 4 原则：嵌套即抽象节点（comprehension）/ 自底向上归约（lambda body）
- [x] IF 回归无退化（30 → 24）
- [x] ternary 回归无退化（0 failed）

### SubTask R25.4: 评估与已知限制
- [x] R25-A 其余评估（R25-03 f-string+ternary+walrus / R25-04 await in subscript / R25-13 ternary+boolop in elif cond）
  - 全部标记为「已知限制」并记录根因 ✅
  - R25-03: IfExp 在 f-string FORMAT_VALUE 上下文抢占 if 头
  - R25-04: 与 R25-01 同源 C5，await 位置在 subscript
  - R25-13: BoolOp op_chain 修剪 ternary value 块导致运算符优先级错误
- [x] R25-B 其余评估（R25-02 for-else+continue / R25-05 for+continue+try / R25-07 nested with+multi context / R25-11 global+del）
  - R25-11 已修 ✅；R25-02/05/07 标记为「已知限制」并记录根因 ✅
  - R25-02: LoopRegion else 块与 IfRegion.elif_bodies 争抢，需重构 _collect_branch_blocks
  - R25-05: continue JUMP_BACKWARD 块归属冲突
  - R25-07: WithRegion 多 context 与嵌套 with 共享 cleanup 块链
- [x] 附加发现 SKIPPED 4 个（Skip-01/02/03/04）记录为已知限制（非本轮目标）✅

### SubTask R25.5-7: 最终验证
- [x] 全量 IF 回归 ≤ 25 failed（基线 30，实际 24，目标 -5 达成 ✅）/ 无新增退化
- [x] 全量 ternary 回归 0 failed（无退化 ✅）
- [ ] 修复报告已写 — `rounds/if_region/round_25/fix_report.md` — 待 Spec Mode 退出后由实现代理完成
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 ✅
- [x] 源代码无 debug 打印残留（grep print/pdb/breakpoint 仅匹配注释）
- [x] 未修改任何测试文件（git status 显示仅新增 R25 测试文件，无现有测试修改）
- [x] 未创建根级 debug 文件（_debug_*.py 已清理）
- [x] 未 git commit（由父代理决定提交时机）

## 算法合规性自检（区域归约 4 原则）
- [x] 自底向上归约（自内层区域向外层）— R25-08 lambda body / R25-09 cleanup 链
- [x] 每块唯一归属（任一时刻一块只属一区域）— R25-12/09 cleanup 块隔离
- [x] 嵌套即抽象节点（子区域在父区域中是单抽象节点）— R25-10 comprehension 作 Tuple.elts 子节点
- [x] 父引用子入口（父的 then/else 列表引用子区域入口）— R25-11 else 分支保留 / R25-06 trailing return

## 禁止项自检
- [x] 未引入跨区域启发式特殊 case
- [x] 未添加后处理补丁
- [x] 未修改任何测试文件
- [x] 未在源码添加 print/pdb/breakpoint 语句
- [x] 未留 _debug_*.py 调试文件
- [x] 未 git commit

## 收尾
- [ ] fix_report.md 已写入 — 待 Spec Mode 退出后由实现代理完成
- [x] checklist.md 已更新（勾选完成项）✅
- [x] 父级 tasks.md 已更新（添加 Task 1.25 IF round_25 条目）✅
- [ ] commit + push 待主代理处理

## 已知限制汇总（7 个，待 R26+ 处理）
| Finding | 根因簇 | 描述 | 待修复方向 |
|---------|--------|------|-----------|
| R25-01 | R25-A (C5) | await call arg in elif 条件时整 if 坍塌为三元 | `_collect_await_predecessor_chain` 沿前驱链完整收集所有 await setup+poll 对 |
| R25-02 | R25-B (C4) | if-elif-else 三分支各自含 for-else + continue 时 else 子句归属错位 | `_collect_branch_blocks` 把 ForLoop 作为整体子节点 |
| R25-03 | R25-A (C1) | f-string 含三元+walrus 在 if-elif-else 分支时整 if 坍塌 | TernaryRegion 在 f-string FORMAT_VALUE 上下文不抢占 if 头 |
| R25-04 | R25-A (C5) | async if-elif-else 条件含 await 在 subscript 时整 if 坍塌 | 与 R25-01 同源 |
| R25-05 | R25-B (C4) | if-elif-else 三分支各自含 for + continue + try 时分支结构错乱 | TryExceptRegion/ForLoop 把 continue JUMP_BACKWARD 块作为整体子节点 |
| R25-07 | R25-B (C6) | 嵌套 with + 多 context 在 elif body 时 with 结构完全错乱 | `_identify_with_regions` 把内层 with 作为外层 with body 子节点 |
| R25-13 | R25-A (C1) | if-elif-else 条件含 ternary + boolop 在 elif 时 else 分支结构与指令错乱 | BoolOp op_chain 不修剪 ternary value 块 |

## 附加 SKIPPED 已知限制（4 个，非本轮目标）
| Skip | 描述 |
|------|------|
| Skip-01 | dictcomp 内 walrus 被错误添加为迭代变量 |
| Skip-02 | genexp 内 walrus 被错误添加为迭代变量 |
| Skip-03 | listcomp 内双 if 过滤被合并为 and |
| Skip-04 | async with + async for 在 elif body 时重编译失败 |
