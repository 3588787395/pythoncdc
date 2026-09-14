# Tasks

- [ ] Task 1: 修复 for/while-else 识别（影响35%函数=96个）
  - [ ] SubTask 1.1: 测试工程师分析 trade_info_utils.pyc (67.50%) 的 for-else 不一致函数，创建10+复现实例
  - [ ] SubTask 1.2: 修复工程师完善 region_analyzer.py 中 LoopRegion 的 else 块识别逻辑
  - [ ] SubTask 1.3: 完善 region_ast_generator.py 中 for-else / while-else 的 AST 生成
  - [ ] SubTask 1.4: 验证受影响pyc文件匹配率提升
  - [ ] SubTask 1.5: quotation.pyc 回归验证
  - [ ] SubTask 1.6: 批量回归验证，提交push

- [ ] Task 2: 修复 try-except-finally 块边界（影响28%函数=76个）
  - [ ] SubTask 2.1: 测试工程师分析 except 块结尾 JUMP_FORWARD 被替换为 return None 的问题
  - [ ] SubTask 2.2: 修复工程师完善 TryExceptRegion 的 handler 出口处理
  - [ ] SubTask 2.3: 完善 try-else 识别
  - [ ] SubTask 2.4: 验证受影响pyc文件匹配率提升
  - [ ] SubTask 2.5: quotation.pyc 回归验证
  - [ ] SubTask 2.6: 批量回归验证，提交push

- [ ] Task 3: 修复 SWAP 指令处理（影响12%函数=32个）
  - [ ] SubTask 3.1: 测试工程师分析 with-as 和比较链中 SWAP 处理错误
  - [ ] SubTask 3.2: 修复工程师完善 ExpressionReconstructor 中 SWAP 指令处理
  - [ ] SubTask 3.3: 验证受影响pyc文件匹配率提升
  - [ ] SubTask 3.4: quotation.pyc 回归验证
  - [ ] SubTask 3.5: 批量回归验证，提交push

- [ ] Task 4: 修复条件跳转反转、类默认值、UNPACK_SEQUENCE等次要问题
  - [ ] SubTask 4.1: 修复条件跳转反转（is None→is not None等）
  - [ ] SubTask 4.2: 修复类默认值元组不匹配
  - [ ] SubTask 4.3: 修复UNPACK_SEQUENCE遗漏
  - [ ] SubTask 4.4: 验证、回归、提交push

- [ ] Task 5: 最终全量验证
  - [ ] SubTask 5.1: 运行全量 batch 验证确认所有 pyc 均为 ok
  - [ ] SubTask 5.2: 确认累计匹配率 100%
  - [ ] SubTask 5.3: 最终提交push

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
