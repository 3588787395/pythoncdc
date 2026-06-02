# Tasks

- [ ] Task 1: 深度根因分析 — 逐个调试7个失败测试的反编译流程
  - [ ] 1.1: n07 try_for_break — 分析 `if v is None: break` 条件反转 + `n = v` 错位 + 多余 `else: return None` 的根因
  - [ ] 1.2: n09 while_try_except — 分析 try-except 后多余 `len(data)` 语句的根因
  - [ ] 1.3: n10a/n10n for_if_for_break — 分析内层 for 不在 if 内 + for-else 混淆 + 重复 if 条件的根因
  - [ ] 1.4: n13a/n13n try_for_if_break_BoolOp — 分析 BoolOp 拆分 + 循环后语句错位 + 多余 return None 的根因
  - [ ] 1.5: n15 while_if_try_except — 分析 `i = 0` 丢失 + 多余 if-else break 的根因

- [ ] Task 2: 修复 n10 for_if_for_break 模式（2个测试）
  - [ ] 2.1: 修复 IfRegion 正确包含内层 LoopRegion（确保内层 for 在 if 条件内）
  - [ ] 2.2: 修复 for-else 与循环后语句的区分（`a = row` 不在 for-else 中）
  - [ ] 2.3: 修复重复生成 if 条件（不再生成 `if len(row) > 0: pass`）
  - [ ] 2.4: 运行 nested 测试验证 n10a/n10n 通过
  - [ ] 2.5: 运行 for_loop 测试确认无回归

- [ ] Task 3: 修复 n07 try_for_break 模式（1个测试）
  - [ ] 3.1: 修复 `if v is None: break` 条件不被反转
  - [ ] 3.2: 修复 `n = v` 作为循环体语句正确生成
  - [ ] 3.3: 修复多余 `else: return None` 不生成
  - [ ] 3.4: 运行 nested 测试验证 n07 通过
  - [ ] 3.5: 运行 for_loop 测试确认无回归

- [ ] Task 4: 修复 n09 while_try_except 模式（1个测试）
  - [ ] 4.1: 修复 try-except 后不生成多余语句
  - [ ] 4.2: 运行 nested 测试验证 n09 通过
  - [ ] 4.3: 运行 for_loop 测试确认无回归

- [ ] Task 5: 修复 n13 try_for_if_break_BoolOp 模式（2个测试）
  - [ ] 5.1: 修复 BoolOp `and` 条件不被拆分为两个独立 if
  - [ ] 5.2: 修复 `a = item` / `n = v` 作为循环体语句（非 else 分支）
  - [ ] 5.3: 修复多余 `else: return None` 不生成
  - [ ] 5.4: 运行 nested 测试验证 n13a/n13n 通过
  - [ ] 5.5: 运行 for_loop 测试确认无回归

- [ ] Task 6: 修复 n15 while_if_try_except 模式（1个测试）
  - [ ] 6.1: 修复 `i = 0` 初始化语句不丢失
  - [ ] 6.2: 修复 `i += 1` 后不生成多余条件判断和 break
  - [ ] 6.3: 运行 nested 测试验证 n15 通过
  - [ ] 6.4: 运行 for_loop 测试确认无回归

- [ ] Task 7: 全量回归验证
  - [ ] 7.1: 运行 `python tests/exhaustive/run_tests.py -t nested` 确认全部通过
  - [ ] 7.2: 运行 `python tests/exhaustive/run_tests.py -t for_loop` 确认无回归
  - [ ] 7.3: 运行全量10区域测试确认无回归

# Task Dependencies
- Task 1 必须先完成（根因分析是所有修复的前提）
- Task 2-6 可部分并行，但建议按顺序执行（2→3→4→5→6），因为修复可能相互影响
- Task 7 依赖 Task 2-6 全部完成
- 每个修复后都必须运行 for_loop 测试确认无回归
