# Tasks

- [x] Task 0: 回滚有回归的变更，恢复到基线 + te046 修复状态
- [x] Task 1: Fix te080 — except handler 内嵌套 try-except
- [x] Task 2: Fix te100 — 三层嵌套 try
- [x] Task 3: Fix try16 — 多层嵌套 try
- [x] Task 4: Fix te081 — try-finally 内嵌套 try-except
- [ ] Task 5: Fix te104 — finally copy 块泄漏
  - [ ] 5.1: 分析 te104 的 region 结构和 try_blocks 内容，确定 cleanup()+return 'val' 块为何在 try_blocks 中
  - [ ] 5.2: 在 region_analyzer 中将 except handler 的 finally copy 块从 try_blocks 移到 handler_blocks，或在 region_ast_generator 的 _generate_try_body 中过滤这些块
  - [ ] 5.3: 验证 te104 反编译输出为 `try: x=1 except ValueError: return 'val' finally: cleanup()`
  - [ ] 5.4: 运行全量回归测试，确认总失败数不超过25f

- [ ] Task 6: Fix try20 — 复杂 try 模式
  - [ ] 6.1: 分析 try20 的字节码和 CFG，确定 `if not result: continue` 为何被反编译为 `if result: pass else: errors.append(result)`
  - [ ] 6.2: 修复 except handler 中 continue 语句的生成（TypeError handler 缺少 continue）
  - [ ] 6.3: 修复条件反转问题（`if not result: continue` → `if result: pass else: ...`）
  - [ ] 6.4: 验证 try20 反编译输出正确
  - [ ] 6.5: 运行全量回归测试，确认总失败数不超过25f

- [ ] Task 7: 最终验证
  - [ ] 7.1: 运行完整 try_except 回归测试，确认 0f
  - [ ] 7.2: 运行全量回归测试，确认总失败数不超过25f
  - [ ] 7.3: 确认 try_except 失败数减少（从原始8f到0f）

# Task Dependencies
- Task 5 (te104) 独立
- Task 6 (try20) 独立
- Task 7 依赖 Task 5 和 Task 6 完成
