# Round 23 Tasks — C7 簇修复（7 测试）+ 回归修复（8 测试）

## 目标（全部达成 ✓）
- C7 簇 7 测试全部修复（7/7 ✓）
- Bug 1/2/3 修复引入的 5+3=8 个回归全部修复（8/8 ✓）
- IF 区域失败数 28 → 21（-7，超目标 ≤23）
- ternary 区域 0 回归（506 passed / 36 skipped / 0 failed）

## 当前进度（已修复 7 主测试 + 8 回归 = 15 测试）
- [x] test_adv18_try_finally_in_if_body ✓（子模式 A：inner_merge both-sink-terminal + 前驱检查）
- [x] test_adv19_try_except_else_in_if_body ✓（子模式 A + B：inner_merge + else_blocks 协调）
- [x] test_adv19_while_else_break_in_elif_body ✓（子模式 B：LoopRegion else_blocks 过滤逻辑修复）
- [x] test_adv19_tuple_unpack_in_if_body ✓（子模式 C：UNPACK_EX 后 trailing 语句丢失修复）
- [x] test_adv20_yield_in_while_in_if_body ✓（子模式 D：trailing_return_none 仅顶层 LoopRegion 过滤）
- [x] test_adv19_multiline_return_in_if_body ✓（模式 3：TernaryRegion 过度延伸进嵌套 IfRegion cond — 三阶段修复）
- [x] test_adv20_walrus_in_while_cond_nested_if ✓（模式 4：walrus 分解多余 'next' 表达式语句）
- [x] test_adv19_multi_not_chain_in_if_cond ✓（模式 F：多 not 链条件 if-elif-else else 分支丢失）
- [x] test_if59ifelifreturn_a/n/x ✓（R-A 回归：return 0 语句丢失 — `_else_has_external_pred` 检查）
- [x] test_adv11_nested_ternary_walrus_cond / test_adv11_walrus_ternary_if_cond ✓（R-B 回归：generated_blocks 守卫）
- [x] test_if84ifchainedcompareelse_a/n/x ✓（R-C 回归：扩展 `_else_has_external_pred` 排除集含 chain_blocks + _else_succ_original）

## 已完成 Tasks

- [x] Task 1: 定位并阅读 `_collect_branch_blocks`（region_analyzer.py:10646-10714）当前实现，确认 BFS 进入子 region 内部块的根因
- [x] Task 2: 修复子模式 A — inner_merge 检测（both-sink-terminal + 外部前驱检查）
- [x] Task 3: 修复子模式 B — else_blocks 协调 + LoopRegion else_blocks 过滤
- [x] Task 4: 修复子模式 C — 嵌套 IfRegion cond 退化为裸表达式 / UNPACK_EX trailing 丢失
- [x] Task 5: 修复子模式 D — 生成器 elif 末尾隐式 return None / walrus 副作用残留
- [x] Task 6: 修复模式 F — 多 not 链条件的 if-elif-else 结构中 else 分支丢失
- [x] Task 9: 修复 Bug 1/2/3 修复引入的回归测试（8 测试 / 3 组）
  - [x] SubTask 9.1: if59 系列（3 测试） — region_analyzer.py:10754-10804 新增 `_else_has_external_pred` 检查
  - [x] SubTask 9.2: adv11 系列（2 测试） — region_ast_generator.py:21460-21474 generated_blocks 守卫
  - [x] SubTask 9.3: if84 系列（3 测试） — region_analyzer.py:10681-10684 + 10803-10818 扩展排除集 `{block, then_succ, else_succ, _else_succ_original} | chain_blocks`
  - [x] SubTask 9.4: 防退化验证 7/7 主测试 + 8/8 回归测试全部通过
- [x] Task 7: 全量回归（IF + ternary），无退化
  - IF: 21 failed / 796 passed / 10 skipped（基线 28/789/10，-7 failed）
  - ternary: 0 failed / 506 passed / 36 skipped（无退化）
- [x] Task 8: 写入 round_23/fix_report.md
- [x] Task 10: 清理调试文件（14 round_23 + 6 根级 = 20 个 _debug/tmp 文件全部删除）

## 算法合规性自检（区域归约 4 原则）
- [x] 自底向上归约：TernaryRegion 与 IfRegion 冲突时按归约顺序决策
- [x] 每块唯一归属：函数级终态块属 final_else（if59）；链式比较中间块属当前 IfRegion（if84）；walrus 副作用属 walrus 表达式（Bug 2）
- [x] 嵌套即抽象节点：TernaryRegion 在 IfRegion 中作单抽象节点（Bug 1 停止 ternary 延伸）
- [x] 父引用子入口：IfRegion 引用 TernaryRegion 入口（adv11 generated_blocks 守卫）
- [x] 无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 展平嵌套 / 硬编码深度上限
