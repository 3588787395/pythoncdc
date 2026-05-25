# Tasks

- [ ] Task 1: Fix te047/te083 — continue→break 误识别
  - [ ] 1.1: 在 `_try_generate_conditional_break_or_continue` 的 continue+normal 路径中，修改 `_has_post_if_stmts` 检查逻辑：当 normal 后继的后续块角色为 EXCEPT_HANDLER 或 EXCEPT_STORE 时，不计入 `_has_post_if_stmts`
  - [ ] 1.2: 或者，当 `_should_skip_transform` 为 True 且 continue_succ 存在时，使用 simple_if 路径生成 `if cond: continue; normal_stmts` 结构（将 continue 放入 then body，normal_stmts 放在 if 之后）
  - [ ] 1.3: 验证 te047/te083 测试通过
  - [ ] 1.4: 运行 try_except 回归测试

- [ ] Task 2: Fix try20 — for-else 多余 return None
  - [ ] 2.1: 在 for 循环 else 生成中（`_generate_loop` 的 else 处理），检测 else_blocks 中的 `return None` 块并过滤。条件：块仅包含 `LOAD_CONST None; RETURN_VALUE` 或 `RETURN_CONST None`，且该块是函数的隐式返回（不是用户代码）
  - [ ] 2.2: 验证 try20 测试通过
  - [ ] 2.3: 运行 try_except + basic + for_loop 回归测试

- [ ] Task 3: Fix try15 — try-return except handler body
  - [ ] 3.1: 在 `_generate_try_body` 中，当 try body 已包含 return 语句时，过滤后续的 `return None` 终端块（`_is_trivial_return` 且 argval is None 的块）
  - [ ] 3.2: 在 `_generate_handler_body_statements` 中，当块包含 `LOAD_GLOBAL/SWAP` 模式后跟 `POP_EXCEPT; RETURN_VALUE` 时，正确生成 `return expr` 而非拆分为 `expr; return`
  - [ ] 3.3: 验证 try15 测试通过
  - [ ] 3.4: 运行 try_except 回归测试

- [ ] Task 4: Fix te104 — finally copy 块泄漏到 try body
  - [ ] 4.1: 在 `_generate_try_body` 的 has_finally 过滤逻辑中，增加检查：如果 try_blocks 中的块的某个前驱在 except_handlers 的 blocks 中，则该块是 handler return 路径上的 finally copy 块，应从 try body 中过滤
  - [ ] 4.2: 将被过滤的 finally copy 块中的 return 语句加入对应的 handler body
  - [ ] 4.3: 验证 te104 测试通过
  - [ ] 4.4: 运行 try_except 回归测试

- [ ] Task 5: Fix try11 — if-else→IfExp 误识别
  - [ ] 5.1: 在 `_generate_try_body` 的 TernaryRegion 处理中，将 IfExp 转换为 If 语句：`{'type': 'If', 'test': expr['test'], 'body': [expr['body']], 'orelse': [expr['orelse']]}` 
  - [ ] 5.2: 验证 try11 测试通过
  - [ ] 5.3: 运行 try_except 回归测试

- [ ] Task 6: Fix te050 — 内层 try-except 在 for 循环中
  - [ ] 6.1: 在循环体生成（`_loop_dispatch_block` 或 `_process_if_blocks`）中，检测属于 TryExceptRegion handler 的块并跳过。具体：当块的 block_role 不是 EXCEPT_HANDLER 但块在某个 TryExceptRegion 的 handler_blocks 中时，跳过该块
  - [ ] 6.2: 验证 te050 测试通过
  - [ ] 6.3: 运行 try_except 回归测试

- [ ] Task 7: Fix te080/te100/try16 — 多层嵌套 try 结构
  - [ ] 7.1: 分析 te080 的 region 结构：内层 TryExceptRegion 的 try_blocks 为空，需要从外层 region 的 try_blocks 中筛选属于内层 try body 的块
  - [ ] 7.2: 改进 `_generate_try_body` 中的嵌套 try 检测逻辑：当内层 TryExceptRegion 的 try_blocks 为空时，根据 handler_entry_blocks 的偏移范围从外层 try_blocks 中筛选内层 try body 块
  - [ ] 7.3: 改进 handler body 生成逻辑：当 handler body 包含嵌套的 TryExceptRegion 时，正确生成嵌套 try-except 结构
  - [ ] 7.4: 验证 te080/te100/try16 测试通过
  - [ ] 7.5: 运行 try_except 回归测试

- [ ] Task 8: Fix te081 — try-finally 内嵌套 try-except
  - [ ] 8.1: 在 finalbody 生成中，检测 finally_blocks 中属于嵌套 TryExceptRegion 的块
  - [ ] 8.2: 当检测到嵌套 TryExceptRegion 时，调用 `_generate_try` 生成嵌套 try-except 结构
  - [ ] 8.3: 验证 te081 测试通过
  - [ ] 8.4: 运行 try_except 回归测试

- [ ] Task 9: 最终验证与清理
  - [ ] 9.1: 运行完整 try_except 回归测试
  - [ ] 9.2: 运行 basic + for_loop + while_loop + if_region 回归测试
  - [ ] 9.3: 确认零回归

# Task Dependencies
- Task 1 (te047/te083) 独立，优先级最高（2个测试）
- Task 2 (try20) 独立，简单修复
- Task 3 (try15) 独立
- Task 4 (te104) 可能依赖 Task 3 的 return 处理逻辑
- Task 5 (try11) 独立
- Task 6 (te050) 独立
- Task 7 (te080/te100/try16) 最复杂，可能需要多轮迭代
- Task 8 (te081) 可能依赖 Task 7 的嵌套 try 修复
- Task 9 依赖所有其他任务完成
