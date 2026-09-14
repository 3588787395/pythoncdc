# Tasks

- [ ] Task 1: 建立迭代基础设施 - 创建轮次目录结构、验证脚本可运行、确认baseline状态
  - [ ] SubTask 1.1: 创建 rounds/ 目录结构（round_01 到 round_10）
  - [ ] SubTask 1.2: 运行 pyc_batch_verify.py stats 确认当前baseline（47 partial, 355 ok）
  - [ ] SubTask 1.3: 确认 quotation.pyc 当前状态

- [ ] Task 2: Round 01 - 测试工程师分析最低匹配率pyc + 修复工程师完善代码
  - [ ] SubTask 2.1: 测试工程师反编译 function.pyc (0.7333) 分析字节码差异，创建10+最小复现实例
  - [ ] SubTask 2.2: 修复工程师根据分析结果完善 region_analyzer.py 和 region_ast_generator.py
  - [ ] SubTask 2.3: 验证 quotation.pyc + 批量回归验证
  - [ ] SubTask 2.4: 提交并push到远程

- [ ] Task 3: Round 02 - 继续下一个最低匹配率pyc
  - [ ] SubTask 3.1: 测试工程师反编译下一pyc分析字节码差异
  - [ ] SubTask 3.2: 修复工程师完善代码
  - [ ] SubTask 3.3: 验证 + 提交push

- [ ] Task 4: Round 03 - 继续迭代
  - [ ] SubTask 4.1: 测试工程师分析
  - [ ] SubTask 4.2: 修复工程师完善
  - [ ] SubTask 4.3: 验证 + 提交push

- [ ] Task 5: Round 04 - 继续迭代
  - [ ] SubTask 5.1: 测试工程师分析
  - [ ] SubTask 5.2: 修复工程师完善
  - [ ] SubTask 5.3: 验证 + 提交push

- [ ] Task 6: Round 05 - 继续迭代
  - [ ] SubTask 6.1: 测试工程师分析
  - [ ] SubTask 6.2: 修复工程师完善
  - [ ] SubTask 6.3: 验证 + 提交push

- [ ] Task 7: Round 06 - 继续迭代
  - [ ] SubTask 7.1: 测试工程师分析
  - [ ] SubTask 7.2: 修复工程师完善
  - [ ] SubTask 7.3: 验证 + 提交push

- [ ] Task 8: Round 07 - 继续迭代
  - [ ] SubTask 8.1: 测试工程师分析
  - [ ] SubTask 8.2: 修复工程师完善
  - [ ] SubTask 8.3: 验证 + 提交push

- [ ] Task 9: Round 08 - 继续迭代
  - [ ] SubTask 9.1: 测试工程师分析
  - [ ] SubTask 9.2: 修复工程师完善
  - [ ] SubTask 9.3: 验证 + 提交push

- [ ] Task 10: Round 09 - 继续迭代
  - [ ] SubTask 10.1: 测试工程师分析
  - [ ] SubTask 10.2: 修复工程师完善
  - [ ] SubTask 10.3: 验证 + 提交push

- [ ] Task 11: Round 10 - 最终迭代
  - [ ] SubTask 11.1: 测试工程师分析
  - [ ] SubTask 11.2: 修复工程师完善
  - [ ] SubTask 11.3: 验证 + 提交push

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 4]
- [Task 6] depends on [Task 5]
- [Task 7] depends on [Task 6]
- [Task 8] depends on [Task 7]
- [Task 9] depends on [Task 8]
- [Task 10] depends on [Task 9]
- [Task 11] depends on [Task 10]
