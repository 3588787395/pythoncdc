# while_loop 5个失败测试修复 - 验证清单

## Phase 1: while13 return None修复
- [ ] 1.1.1: while13的LoopRegion `has_trailing_return_none`属性确认
- [ ] 1.1.2: `_else_return_none_as_post`逻辑在函数体嵌套code object场景下正确触发
- [ ] 1.1.3: test_while13_while_return 通过（16 vs 16指令匹配）

## Phase 2: while15 嵌套while重复pre_stmts修复
- [ ] 2.1.1: `_cond_was_generated=True`时跳过条件块指令迭代循环
- [ ] 2.1.2: 条件表达式在`_cond_was_generated=True`时仍正确重建
- [ ] 2.1.3: test_while15_nested_while 通过（33 vs 33指令匹配）
- [ ] 2.1.4: test_wl07nestedwhile_a_b 仍通过（不回归）
- [ ] 2.1.5: test_wl07nestedwhile_n_m 仍通过（不回归）
- [ ] 2.1.6: test_wl07nestedwhile_x_y 仍通过（不回归）

## Phase 3: wl32 多break else:continue误生成修复
- [ ] 3.1.1: else后继含有效指令时不生成`else: continue`
- [ ] 3.1.2: else后继的有效指令被正确生成为循环体语句
- [ ] 3.1.3: test_wl32whilemultibreak_n 通过（27 vs 27指令匹配）
- [ ] 3.1.4: test_wl32whilemultibreak_x 通过（27 vs 27指令匹配）

## Phase 4: while20 elif链断裂修复
- [ ] 4.1.1: while20的IfRegion elif链结构确认
- [ ] 4.1.2: 循环体内IfRegion elif链AST生成逻辑修复
- [ ] 4.1.3: test_while20_complex_state_machine 通过（47 vs 47指令匹配）

## Phase 5: 回归验证
- [ ] 5.1.1: while_loop全量测试 0f
- [ ] 5.1.2: basic全量测试 0f
- [ ] 5.1.3: for_loop全量测试 ≤7f
- [ ] 5.1.4: 全量10区域回归测试无回归
