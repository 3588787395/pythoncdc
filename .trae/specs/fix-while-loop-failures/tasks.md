# Tasks

## Phase 1: while13 return None修复
- [ ] Task 1.1: 诊断while13 return None丢失根因
  - [ ] 1.1.1: 检查while13的LoopRegion是否设置了`has_trailing_return_none`
  - [ ] 1.1.2: 检查`_else_return_none_as_post`逻辑是否在函数体嵌套code object场景下正确触发
  - [ ] 1.1.3: 确认return None的生成路径（是否被函数体return处理覆盖）
- [ ] Task 1.2: 实施修复
  - [ ] 1.2.1: 修复`_loop_generate_while`中`_else_return_none_as_post`逻辑确保return None正确生成
  - [ ] 1.2.2: 验证test_while13_while_return通过

## Phase 2: while15 嵌套while重复pre_stmts修复
- [ ] Task 2.1: 修复`_cond_was_generated`处理逻辑
  - [ ] 2.1.1: 当`_cond_was_generated=True`时，跳过整个条件块指令迭代循环（而非仅事后清空pre_stmts）
  - [ ] 2.1.2: 确保`_cond_was_generated=True`时条件表达式仍能正确重建
  - [ ] 2.1.3: 验证test_while15_nested_while通过
  - [ ] 2.1.4: 验证test_wl07nestedwhile系列仍通过（不回归）

## Phase 3: wl32 多break else:continue误生成修复
- [ ] Task 3.1: 修复`_try_generate_conditional_break_or_continue`中else:continue误生成
  - [ ] 3.1.1: 当else后继是循环回边块且含有效指令时，不生成`else: continue`
  - [ ] 3.1.2: 确保else后继的有效指令（如`n += 1`）被正确生成为循环体语句
  - [ ] 3.1.3: 验证test_wl32whilemultibreak_n通过
  - [ ] 3.1.4: 验证test_wl32whilemultibreak_x通过

## Phase 4: while20 elif链断裂修复
- [ ] Task 4.1: 修复while循环体内elif链生成
  - [ ] 4.1.1: 分析while20的IfRegion结构和elif链识别
  - [ ] 4.1.2: 修复循环体内IfRegion elif链的AST生成逻辑
  - [ ] 4.1.3: 验证test_while20_complex_state_machine通过

## Phase 5: 回归验证
- [ ] Task 5.1: 运行while_loop全量测试验证0f
- [ ] Task 5.2: 运行basic测试验证0f
- [ ] Task 5.3: 运行for_loop测试验证≤7f
- [ ] Task 5.4: 运行全量10区域回归测试

# Task Dependencies
- Task 1-4 可并行（独立修复）
- Task 5 依赖 Task 1-4 全部完成
