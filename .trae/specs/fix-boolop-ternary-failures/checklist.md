# BoolOp/Ternary 区域失败测试修复 - 验证清单

## Phase 1: BoolOp修复验证

### Task 1.1: bo24混合and/or链修复
- [ ] 1.1.1: `_build_boolop_expression`中非op_chain块的短路跳转检测逻辑已添加
- [ ] 1.1.2: 检测到的and/or短路块被插入正确的segment位置
- [ ] 1.1.3: test_bo24orandor_a_b_c 通过
- [ ] 1.1.4: test_bo24orandor_n_m_i 通过
- [ ] 1.1.5: test_bo24orandor_x_y_z 通过

### Task 1.2: bo43 UNARY_NOT处理修复
- [ ] 1.2.1: UNARY_NOT块后的JUMP_IF_TRUE_OR_POP被识别为or操作
- [ ] 1.2.2: UNARY_NOT操作符被正确包装到子表达式中
- [ ] 1.2.3: test_bo43complexnotandor_a_b_c_d 通过

## Phase 2: Ternary修复验证

### Task 2.1: ternary11 if条件中的ternary修复
- [ ] 2.1.1: `_if_extract_condition_from_instructions`中TernaryRegion merge_ctx='compare'检测已添加
- [ ] 2.1.2: ternary表达式与后续COMPARE_OP组合为Compare节点
- [ ] 2.1.3: test_ternary11_in_if 通过

### Task 2.2: ternary13 for迭代器中的ternary修复
- [ ] 2.2.1: `_loop_generate_for`中TernaryRegion merge_ctx='iter'查找逻辑已改进
- [ ] 2.2.2: IfExp表达式被正确设为iter_expr
- [ ] 2.2.3: test_ternary13_in_for_iter 通过

### Task 2.3: ternary15 try块中的ternary赋值修复
- [ ] 2.3.1: TernaryRegion在try块中不被重复生成
- [ ] 2.3.2: value_target被正确检测
- [ ] 2.3.3: test_ternary15_in_try 通过

### Task 2.4: te04 ternary作为函数参数修复
- [ ] 2.4.1: 连续ternary表达式被合并为Call节点的参数
- [ ] 2.4.2: test_te04ternaryfuncparam_a 通过
- [ ] 2.4.3: test_te04ternaryfuncparam_n 通过

## Phase 3: 全量验证

### 回归测试
- [ ] 3.1.1: boolop测试套件无回归（9f基线，预期≤6f）
- [ ] 3.1.2: ternary测试套件无回归（8f基线，预期≤5f）
- [ ] 3.1.3: 全量10区域测试无回归（基线199f）

### 不可修复测试确认
- [ ] 3.2.1: bo31 (3f) 确认需region_analyzer修改
- [ ] 3.2.2: bo42 (1f) 确认需region_analyzer修改
- [ ] 3.2.3: bo50 (1f) 确认需region_analyzer修改
- [ ] 3.2.4: ternary12 (1f) 确认需region_analyzer修改
- [ ] 3.2.5: ternary17 (1f) 确认需region_analyzer修改
- [ ] 3.2.6: ternary20 (1f) 确认需code_generator修改
