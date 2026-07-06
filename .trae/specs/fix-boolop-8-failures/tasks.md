# Tasks

## Phase 1: bo24 混合短路+条件跳转链修复

- [ ] Task 1.1: 修改 `_detect_boolop_short_circuit_chain` 支持混合跳转类型
  - [ ] 1.1.1: 在链遍历中，当当前块是SHORT_CIRCUIT_JUMP_OPS而fall-through后继是FORWARD_CONDITIONAL_JUMP_OPS时，继续链检测
  - [ ] 1.1.2: 正确设置混合链中条件跳转块的操作符类型（'FALSE'→'and', 'TRUE'→'or'）
  - [ ] 1.1.3: 验证bo24×3测试通过
  - [ ] 1.1.4: 验证bo17/bo18等while-boolop测试无回归

## Phase 2: bo31 if条件中的and链修复

- [ ] Task 2.1: 修改 `_detect_boolop_conditional_chain` 放宽同目标检查
  - [ ] 2.1.1: 添加 `_is_trivial_block` 方法（仅含LOAD_CONST+RETURN_VALUE的块）
  - [ ] 2.1.2: 当两个跳转目标都是trivial block时，不中断链
  - [ ] 2.1.3: 在 `all_same_target` 检查中也放宽trivial block的目标差异
  - [ ] 2.1.4: 验证bo31×3测试通过
  - [ ] 2.1.5: 验证if_region测试无回归

## Phase 3: bo43 UNARY_NOT处理修复

- [ ] Task 3.1: 修改 `_build_boolop_expression` 正确处理UNARY_NOT和非chain前驱
  - [ ] 3.1.1: 在构建chain块表达式时，检查fall-through前驱是否不在chain中
  - [ ] 3.1.2: 将非chain前驱的表达式与当前chain块的表达式合并（如 LOAD_NAME(b) + UNARY_NOT → UnaryOp(not, Name(b))）
  - [ ] 3.1.3: 修改分段逻辑，正确处理and→or和or→and转换（引入outer_op追踪）
  - [ ] 3.1.4: 验证bo43测试通过
  - [ ] 3.1.5: 验证bo23/bo51等混合and/or测试无回归

## Phase 4: bo42 列表推导式and条件合并

- [ ] Task 4.1: 修改 `_extract_comp_ifs` 合并连续and条件
  - [ ] 4.1.1: 检测连续的POP_JUMP_BACKWARD_IF_FALSE跳转到同一循环头部
  - [ ] 4.1.2: 将连续的and条件合并为单个BoolOp(and, [...])表达式
  - [ ] 4.1.3: 验证bo42测试通过
  - [ ] 4.1.4: 验证其他列表推导式测试无回归

## Phase 5: 全量验证

- [ ] Task 5.1: 运行boolop全部测试验证修复效果
- [ ] Task 5.2: 运行for_loop测试确保无回归
- [ ] Task 5.3: 运行if_region测试确保无回归

# Task Dependencies
- Task 1.1 和 2.1 和 3.1 可并行（独立的修复）
- Task 4.1 依赖 1.1（如果需要在region_analyzer中支持BACKWARD跳转）
- Task 5.x 依赖 1.x-4.x 全部完成
