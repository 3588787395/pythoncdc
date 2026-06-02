# Tasks

- [ ] Task 0: 回滚有回归的变更，恢复到基线 + te046 修复状态
  - [ ] 0.1: 回滚 region_analyzer.py 中 inner_handler_indices 的 PUSH_EXC_INFO 检查
  - [ ] 0.2: 回滚 region_analyzer.py 中 known_handler_starts 过滤逻辑
  - [ ] 0.3: 回滚 region_analyzer.py 中 _collect_body 跳过 TryExceptRegion 块的逻辑
  - [ ] 0.4: 回滚 region_ast_generator.py 中 _generate_try 嵌套 TryExceptRegion 检测逻辑
  - [ ] 0.5: 验证回滚后 try_except 恢复到 8f（基线状态），te046 仍通过
  - [ ] 0.6: 验证 for_loop 保持 3f，if_region 保持 0f

- [ ] Task 1: Fix te080 — except handler 内嵌套 try-except
  - [ ] 1.1: 分析 te080 的异常表条目和 region 结构，确定 inner_handler_indices 为何将内层 handler 标记为 inner
  - [ ] 1.2: 修改 inner_handler_indices 逻辑：当 handler 块以 PUSH_EXC_INFO 开头且其 try_start >= 外层 handler_start 时，不标记为 inner handler（而是作为独立的嵌套 try-except）
  - [ ] 1.3: 在 generate 方法的 is_contained 检查中，添加 TryExceptRegion 嵌套包含检查：当内层 TryExceptRegion 的 entry 在外层 TryExceptRegion 的 handler 范围内时，标记为 contained
  - [ ] 1.4: 在 _generate_try 的 handler body 生成中，检测并生成嵌套的 TryExceptRegion
  - [ ] 1.5: 验证 te080 测试通过
  - [ ] 1.6: 验证 te10/te25 无回归
  - [ ] 1.7: 验证 for_loop 保持 3f，if_region 保持 0f

- [ ] Task 2: Fix te100 — 三层嵌套 try
  - [ ] 2.1: 分析 te100 的异常表条目和 region 结构
  - [ ] 2.2: 修复异常表条目合并逻辑或 region 创建逻辑
  - [ ] 2.3: 验证 te100 测试通过
  - [ ] 2.4: 验证 te10/te25 无回归
  - [ ] 2.5: 验证 for_loop 保持 3f，if_region 保持 0f

- [ ] Task 3: Fix try16 — 多层嵌套 try
  - [ ] 3.1: 分析 try16 的异常表条目和 region 结构
  - [ ] 3.2: 修复多层嵌套 try 的 region 创建和 AST 生成
  - [ ] 3.3: 验证 try16 测试通过
  - [ ] 3.4: 验证无回归

- [ ] Task 4: Fix te081 — try-finally 内嵌套 try-except
  - [ ] 4.1: 分析 te081 的 region 结构，确定 finally body 中 try-except 未被识别的原因
  - [ ] 4.2: 在 finalbody 生成中检测嵌套 TryExceptRegion
  - [ ] 4.3: 验证 te081 测试通过
  - [ ] 4.4: 验证无回归

- [ ] Task 5: Fix te104 — finally copy 块泄漏
  - [ ] 5.1: 分析 te104 的 try_blocks 结构，确定 finally copy 块被错误放入 try body 的原因
  - [ ] 5.2: 在 _generate_try_body 中过滤 finally copy 块
  - [ ] 5.3: 验证 te104 测试通过
  - [ ] 5.4: 验证无回归

- [ ] Task 6: Fix try15 — except handler return 语句
  - [ ] 6.1: 在 handler body 生成中检测 SWAP+POP_EXCEPT+RETURN_VALUE 模式
  - [ ] 6.2: 生成 return expr 而非 expr; return None
  - [ ] 6.3: 验证 try15 测试通过
  - [ ] 6.4: 验证无回归

- [ ] Task 7: Fix try20 — 复杂 try 模式
  - [ ] 7.1: 分析 try20 的具体问题
  - [ ] 7.2: 修复 for-else 中多余的 return None
  - [ ] 7.3: 修复条件反转等问题
  - [ ] 7.4: 验证 try20 测试通过
  - [ ] 7.5: 验证无回归

- [ ] Task 8: 最终验证与清理
  - [ ] 8.1: 运行完整 try_except 回归测试，确认 0f
  - [ ] 8.2: 运行 for_loop 回归测试，确认保持 3f
  - [ ] 8.3: 运行 if_region 回归测试，确认保持 0f
  - [ ] 8.4: 运行 basic + while_loop 回归测试，确认无回归

# Task Dependencies
- Task 0 优先级最高，必须先完成回滚
- Task 1 (te080) 是最复杂的嵌套 try 修复，其他嵌套 try 修复可能依赖它
- Task 2 (te100) 依赖 Task 1 的嵌套 try 修复
- Task 3 (try16) 依赖 Task 1 的嵌套 try 修复
- Task 4 (te081) 可能依赖 Task 1 的嵌套 try 修复
- Task 5 (te104) 独立
- Task 6 (try15) 独立
- Task 7 (try20) 可能依赖 Task 1 和 Task 6
- Task 8 依赖所有其他任务完成
