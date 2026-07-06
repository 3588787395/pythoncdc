# BoolOp 8个失败测试修复 - 验证清单

## Phase 1: bo24修复验证
- [ ] 1.1.1: `_detect_boolop_short_circuit_chain` 支持FORWARD_CONDITIONAL_JUMP_OPS后继
- [ ] 1.1.2: test_bo24orandor_a_b_c 通过
- [ ] 1.1.3: test_bo24orandor_n_m_i 通过
- [ ] 1.1.4: test_bo24orandor_x_y_z 通过
- [ ] 1.1.5: bo17/bo18 while-boolop测试无回归

## Phase 2: bo31修复验证
- [ ] 2.1.1: `_is_trivial_block` 方法已添加
- [ ] 2.1.2: 同目标检查对trivial block放宽
- [ ] 2.1.3: test_bo31andinif_a_b 通过
- [ ] 2.1.4: test_bo31andinif_n_m 通过
- [ ] 2.1.5: test_bo31andinif_x_y 通过
- [ ] 2.1.6: if_region测试无回归

## Phase 3: bo43修复验证
- [ ] 3.1.1: `_build_boolop_expression` 正确处理非chain前驱的表达式合并
- [ ] 3.1.2: 分段逻辑正确处理and→or和or→and转换
- [ ] 3.1.3: test_bo43complexnotandor_a_b_c_d 通过
- [ ] 3.1.4: bo23/bo51混合and/or测试无回归

## Phase 4: bo42修复验证
- [ ] 4.1.1: `_extract_comp_ifs` 合并连续POP_JUMP_BACKWARD_IF_FALSE为BoolOp(and)
- [ ] 4.1.2: test_bo42boolopinlistcomp_items 通过
- [ ] 4.1.3: 其他列表推导式测试无回归

## Phase 5: 全量验证
- [ ] 5.1: boolop测试套件通过率 ≥ 132/132 (100%)
- [ ] 5.2: for_loop测试无回归
- [ ] 5.3: if_region测试无回归
