# Tasks

## Phase 1: BoolOp修复

- [ ] Task 1.1: 修复bo24混合and/or链 — `_build_boolop_expression` segment构建
  - [ ] 1.1.1: 分析bo24字节码结构，确认op_chain缺少and短路块
  - [ ] 1.1.2: 在`_build_boolop_expression`中添加非op_chain块的短路跳转检测逻辑
  - [ ] 1.1.3: 将检测到的and/or短路块插入正确的segment位置
  - [ ] 1.1.4: 验证bo24×3测试通过

- [ ] Task 1.2: 修复bo43 UNARY_NOT处理 — `_build_boolop_expression` UNARY_NOT
  - [ ] 1.2.1: 分析bo43字节码结构，确认UNARY_NOT块的处理流程
  - [ ] 1.2.2: 修复UNARY_NOT块后的JUMP_IF_TRUE_OR_POP被识别为or操作
  - [ ] 1.2.3: 确保UNARY_NOT操作符被正确包装到子表达式中
  - [ ] 1.2.4: 验证bo43测试通过

## Phase 2: Ternary修复

- [ ] Task 2.1: 修复ternary11 if条件中的ternary — `_if_extract_condition_from_instructions`
  - [ ] 2.1.1: 在`_if_extract_condition_from_instructions`中添加TernaryRegion merge_ctx='compare'检测
  - [ ] 2.1.2: 提取ternary表达式并与后续COMPARE_OP组合为Compare节点
  - [ ] 2.1.3: 处理NONE_CHECK_OPS（如`if (a if c else b) is not None`）
  - [ ] 2.1.4: 验证ternary11测试通过

- [ ] Task 2.2: 修复ternary13 for迭代器中的ternary — `_loop_generate_for`
  - [ ] 2.2.1: 改进`_loop_generate_for`中TernaryRegion merge_ctx='iter'的查找逻辑
  - [ ] 2.2.2: 当for_iter_setup块不存在时，在ast_nodes中查找IfExp表达式
  - [ ] 2.2.3: 将找到的IfExp从ast_nodes中移除并设为iter_expr
  - [ ] 2.2.4: 验证ternary13测试通过

- [ ] Task 2.3: 修复ternary15 try块中的ternary赋值
  - [ ] 2.3.1: 防止TernaryRegion在try块中被重复生成
  - [ ] 2.3.2: 在else分支中检测value_target（STORE指令）
  - [ ] 2.3.3: 验证ternary15测试通过

- [ ] Task 2.4: 修复te04 ternary作为函数参数
  - [ ] 2.4.1: 分析te04字节码结构，确认两个ternary的func_call_info
  - [ ] 2.4.2: 改进连续ternary表达式的合并逻辑
  - [ ] 2.4.3: 验证te04×2测试通过

## Phase 3: 验证

- [ ] Task 3.1: 运行boolop和ternary测试套件验证修复效果
- [ ] Task 3.2: 运行全量10区域回归测试
- [ ] Task 3.3: 更新tasks.md/checklist.md

# Task Dependencies
- Task 1.1 和 1.2 可并行（独立的boolop修复）
- Task 2.1-2.4 可并行（独立的ternary修复）
- Task 3.x 依赖 1.x 和 2.x 全部完成
