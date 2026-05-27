# Tasks

- [ ] Task 1: Fix te047/te083 — continue→break 误识别（fall_through 选择异常处理入口块）
  - [ ] 1.1: 在 `_try_generate_conditional_break_or_continue` 中修改 fall_through 选择逻辑：当后继块包含 PUSH_EXC_INFO 或 WITH_EXCEPT_START 指令时，跳过该后继，选择另一个非 jump_target 的后继作为 fall_through
  - [ ] 1.2: 如果所有非 jump_target 后继都是异常处理入口，则回退到原始逻辑（选择第一个非 jump_target 后继）
  - [ ] 1.3: 验证 te047 和 te083 测试通过
  - [ ] 1.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 2: Fix te050 — 内层 try-except 在 for 循环中未识别
  - [ ] 2.1: 分析 te050 的 region 结构和异常表，确定内层 try-except 未被识别的原因
  - [ ] 2.2: 修改 `_find_actual_handler_start` 添加 bare except 检测（PUSH_EXC_INFO 无 CHECK_EXC_MATCH/CHECK_EG_MATCH 且无 RERAISE 时，返回 cleanup_offset）
  - [ ] 2.3: 验证 te050 测试通过
  - [ ] 2.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 3: Fix te080/try16 — 嵌套 try-except 异常表解析
  - [ ] 3.1: 在 `_parse_exception_table` 中添加向后搜索逻辑：当 except handler 的 `try_start >= handler_start` 时，向后搜索实际的 try body 起始位置
  - [ ] 3.2: 在 `_find_actual_handler_start` 中添加候选者收集逻辑，选择最接近 try_start 的候选者（offset <= try_start 中最大的）
  - [ ] 3.3: 在 `_parse_exception_table` 的合并逻辑中，修复 try_end 不超过 handler_start 的约束
  - [ ] 3.4: 验证 te080 和 try16 测试通过
  - [ ] 3.5: 运行 try_except 回归测试，确认无回归

- [ ] Task 4: Fix te100 — 三层嵌套 try handler 顺序错误
  - [ ] 4.1: 分析 te100 的异常表条目和 region 结构，确定 handler 顺序错误的原因
  - [ ] 4.2: 修复异常表条目合并逻辑或 region 创建逻辑
  - [ ] 4.3: 验证 te100 测试通过
  - [ ] 4.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 5: Fix te104 — finally copy 块泄漏到 try body
  - [ ] 5.1: 在 `_generate_try_body` 的 has_finally 过滤逻辑中，增加检查：如果 try_blocks 中的块的某个前驱在 except_handlers 的 blocks 中，则该块是 handler return 路径上的 finally copy 块，应从 try body 中过滤
  - [ ] 5.2: 将被过滤的 finally copy 块中的 return 语句加入对应的 handler body
  - [ ] 5.3: 验证 te104 测试通过
  - [ ] 5.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 6: Fix try15 — except handler return 语句错误
  - [ ] 6.1: 在 handler body 生成中，检测 `LOAD_X; SWAP; POP_EXCEPT; RETURN_VALUE` 模式并生成 `return expr`
  - [ ] 6.2: 验证 try15 测试通过
  - [ ] 6.3: 运行 try_except 回归测试，确认无回归

- [ ] Task 7: Fix te081 — try-finally 内嵌套 try-except
  - [ ] 7.1: 在 finalbody 生成中，检测 finally_blocks 中属于嵌套 TryExceptRegion 的块
  - [ ] 7.2: 当检测到嵌套 TryExceptRegion 时，调用 `_generate_try` 生成嵌套 try-except 结构
  - [ ] 7.3: 验证 te081 测试通过
  - [ ] 7.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 8: Fix try20 — 复杂 try 模式
  - [ ] 8.1: 分析 try20 的具体问题（条件反转、for-else 多余 return、continue 处理）
  - [ ] 8.2: 修复 for-else 中 return None 过滤
  - [ ] 8.3: 验证 try20 测试通过
  - [ ] 8.4: 运行 try_except 回归测试，确认无回归

- [ ] Task 9: 最终验证与清理
  - [ ] 9.1: 运行完整 try_except 回归测试
  - [ ] 9.2: 运行 basic + for_loop + while_loop + if_region 回归测试
  - [ ] 9.3: 确认零回归（回归不超过5个）

# Task Dependencies
- Task 1 (te047/te083) 独立，优先级最高
- Task 2 (te050) 可能依赖 Task 1 的 fall_through 修复
- Task 3 (te080/try16) 独立但最复杂
- Task 4 (te100) 可能依赖 Task 3 的异常表修复
- Task 5 (te104) 独立
- Task 6 (try15) 独立
- Task 7 (te081) 可能依赖 Task 3 的嵌套 try 修复
- Task 8 (try20) 可能依赖 Task 1 和 Task 6 的修复
- Task 9 依赖所有其他任务完成
