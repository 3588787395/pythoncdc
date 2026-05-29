# Tasks

## 紧急修复：消除回归bug
- [ ] Task 0: 修复 `_loop_generate_for` 中 `_trailing_return_none_stmts` 未定义bug
  - [ ] 0.1: 在 `_loop_generate_for` 方法中添加 `_trailing_return_none_stmts = []` 初始化
  - [ ] 0.2: 添加与 `_loop_generate_while` 一致的 `has_trailing_return_none` 检查逻辑
  - [ ] 0.3: 运行nested区域测试确认崩溃消除（127f→~20f）
  - [ ] 0.4: 运行全量10区域回归测试确认零回归

## 修复1: BoolOp在If内部被错误展平 (nested_if_boolop, 3f)
- [ ] Task 1: 修复 nested_if_boolop_v1/v2/v3
  - [ ] 1.1: 运行3个失败测试获取详细错误信息（JUMP_IF_FALSE_OR_POP vs STORE_NAME）
  - [ ] 1.2: 在源码中定位BoolOpRegion在IfRegion内部的生成路径
  - [ ] 1.3: 实施修复（在_process_if_blocks或_generate_boolop中）
  - [ ] 1.4: 运行nested区域测试验证改善
  - [ ] 1.5: 运行全量回归测试确认零回归

## 修复2: With在If内部生成错误结构 (nested_if_with, 3f)
- [ ] Task 2: 修复 nested_if_with_v1/v2/v3
  - [ ] 2.1: 运行3个失败测试获取详细错误信息（多余5条指令）
  - [ ] 2.2: 在源码中定位WithRegion在IfRegion内部的生成路径
  - [ ] 2.3: 实施修复
  - [ ] 2.4: 运行nested区域测试验证改善
  - [ ] 2.5: 运行全量回归测试确认零回归

## 修复3: 嵌套while break归属错误 (n23, 3f)
- [ ] Task 3: 修复 n23whileinwhilebreak_a/b/n
  - [ ] 3.1: 运行3个失败测试获取详细错误信息（多余13条指令）
  - [ ] 3.2: 分析内层while break跳转到外层的字节码模式
  - [ ] 3.3: 实施修复
  - [ ] 3.4: 运行nested区域测试验证改善
  - [ ] 3.5: 运行全量回归测试确认零回归

## 修复4: while-if-while-break (n11, 2f)
- [ ] Task 4: 修复 n11while_if_while_break_a/n
  - [ ] 4.1: 运行2个失败测试获取详细错误信息
  - [ ] 4.2: 分析嵌套while-if-while结构中break归属
  - [ ] 4.3: 实施修复
  - [ ] 4.4: 运行nested区域测试验证改善
  - [ ] 4.5: 运行全量回归测试确认零回归

## 修复5: try-for-if-break (n13, 2f)
- [ ] Task 5: 修复 n13try_for_if_break_a/n
  - [ ] 5.1: 运行2个失败测试获取详细错误信息
  - [ ] 5.2: 分析try内for循环if break归属
  - [ ] 5.3: 实施修复
  - [ ] 5.4: 运行nested区域测试验证改善
  - [ ] 5.5: 运行全量回归测试确认零回归

## 修复6: for-if-for-break (n10, 2f)
- [ ] Task 6: 修复 n10for_if_for_break_a/n
  - [ ] 6.1: 运行2个失败测试获取详细错误信息
  - [ ] 6.2: 分析嵌套for-if-for结构中break归属
  - [ ] 6.3: 实施修复
  - [ ] 6.4: 运行nested区域测试验证改善
  - [ ] 6.5: 运行全量回归测试确认零回归

## 修复7: while-try-except多余指令 (n09, 2f)
- [ ] Task 7: 修复 n09while_try_except_a/n
  - [ ] 7.1: 运行2个失败测试获取详细错误信息
  - [ ] 7.2: 分析while内try-except多余指令根因
  - [ ] 7.3: 实施修复
  - [ ] 7.4: 运行nested区域测试验证改善
  - [ ] 7.5: 运行全量回归测试确认零回归

## 修复8: try-for-break差1条指令 (n07, 1f)
- [ ] Task 8: 修复 n07try_for_break_n
  - [ ] 8.1: 运行1个失败测试获取详细错误信息
  - [ ] 8.2: 分析try内for break差1条指令根因
  - [ ] 8.3: 实施修复
  - [ ] 8.4: 运行nested区域测试验证改善
  - [ ] 8.5: 运行全量回归测试确认零回归

## 修复9: while-if-try-except多余指令 (n15, 2f)
- [ ] Task 9: 修复 n15while_if_try_except_a/n
  - [ ] 9.1: 运行2个失败测试获取详细错误信息
  - [ ] 9.2: 分析while-if-try-except多余指令根因
  - [ ] 9.3: 实施修复
  - [ ] 9.4: 运行nested区域测试验证改善
  - [ ] 9.5: 运行全量回归测试确认零回归

## 最终验证
- [ ] Task 10: 全量回归验证与文档更新
  - [ ] 10.1: 运行全量10区域回归测试
  - [ ] 10.2: 确认nested区域失败数从27f降至≤10f
  - [ ] 10.3: 确认其他9个区域零回归
  - [ ] 10.4: 更新tasks.md/checklist.md/spec.md

# Task Dependencies
- Task 0 必须最先完成（消除崩溃，恢复测试基线）
- Task 1-9 可部分并行，但每次修改后必须运行全量回归
- Task 1 (BoolOp) 和 Task 2 (With) 可并行
- Task 3-6 (break归属) 可能共享根因，建议串行
- Task 7-9 (try-except相关) 可能共享根因，建议串行
- Task 10 依赖 Task 0-9 全部完成
