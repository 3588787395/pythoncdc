# 修复Nested区域剩余20个失败测试 - 验证清单

## 紧急修复验证
- [ ] Task 0: `_loop_generate_for` 中 `_trailing_return_none_stmts` 未定义bug修复
  - [ ] 0.1: `_loop_generate_for` 中添加 `_trailing_return_none_stmts = []` 初始化
  - [ ] 0.2: for循环else块 `has_trailing_return_none` 检查逻辑与while一致
  - [ ] 0.3: nested区域测试从127f降至~20f（崩溃消除）
  - [ ] 0.4: 全量10区域回归测试零回归

## 修复1验证: BoolOp在If内部 (nested_if_boolop, 3f)
- [ ] 1.1: nested_if_boolop_v1 通过
- [ ] 1.2: nested_if_boolop_v2 通过
- [ ] 1.3: nested_if_boolop_v3 通过
- [ ] 1.4: 全量10区域回归测试零回归

## 修复2验证: With在If内部 (nested_if_with, 3f)
- [ ] 2.1: nested_if_with_v1 通过
- [ ] 2.2: nested_if_with_v2 通过
- [ ] 2.3: nested_if_with_v3 通过
- [ ] 2.4: 全量10区域回归测试零回归

## 修复3验证: 嵌套while break (n23, 3f)
- [ ] 3.1: n23whileinwhilebreak_a 通过
- [ ] 3.2: n23whileinwhilebreak_b 通过
- [ ] 3.3: n23whileinwhilebreak_n 通过
- [ ] 3.4: 全量10区域回归测试零回归

## 修复4验证: while-if-while-break (n11, 2f)
- [ ] 4.1: n11while_if_while_break_a 通过
- [ ] 4.2: n11while_if_while_break_n 通过
- [ ] 4.3: 全量10区域回归测试零回归

## 修复5验证: try-for-if-break (n13, 2f)
- [ ] 5.1: n13try_for_if_break_a 通过
- [ ] 5.2: n13try_for_if_break_n 通过
- [ ] 5.3: 全量10区域回归测试零回归

## 修复6验证: for-if-for-break (n10, 2f)
- [ ] 6.1: n10for_if_for_break_a 通过
- [ ] 6.2: n10for_if_for_break_n 通过
- [ ] 6.3: 全量10区域回归测试零回归

## 修复7验证: while-try-except (n09, 2f)
- [ ] 7.1: n09while_try_except_a 通过
- [ ] 7.2: n09while_try_except_n 通过（如果存在）
- [ ] 7.3: 全量10区域回归测试零回归

## 修复8验证: try-for-break (n07, 1f)
- [ ] 8.1: n07try_for_break_n 通过
- [ ] 8.2: 全量10区域回归测试零回归

## 修复9验证: while-if-try-except (n15, 2f)
- [ ] 9.1: n15while_if_try_except_a 通过
- [ ] 9.2: n15while_if_try_except_n 通过（如果存在）
- [ ] 9.3: 全量10区域回归测试零回归

## 最终验证
- [ ] 10.1: 全量10区域回归测试通过
- [ ] 10.2: nested区域失败数从27f降至≤10f
- [ ] 10.3: for_loop区域零回归（红线指标）
- [ ] 10.4: 所有修改仅在region_ast_generator.py（除非必要且验证安全）
