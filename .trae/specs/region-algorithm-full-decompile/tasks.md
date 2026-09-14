# Tasks

- [ ] Task 1: 建立基线 - 运行 pyc_batch_verify.py stats 记录当前基线（348 ok, 54 partial, 96.7%）
- [ ] Task 2: 对 54 个 partial pyc 按匹配率从低到高排序，建立优先级队列
- [ ] Task 3: Round 1 - 测试工程师分析 trade_info_utils.pyc（最低率 70%）
  - [ ] SubTask 3.1: 反编译 trade_info_utils.pyc，验证字节码一致性
  - [ ] SubTask 3.2: 分析不一致函数，归类失败模式
  - [ ] SubTask 3.3: 创建 10+ 最小复现实例
- [ ] Task 4: Round 1 - 修复工程师根据分析结果修复代码
  - [ ] SubTask 4.1: 修复区域识别/AST 生成缺陷
  - [ ] SubTask 4.2: 在方法注释中写入反编译逻辑
  - [ ] SubTask 4.3: 验证最小复现实例全部通过
- [ ] Task 5: Round 1 - 验证与提交
  - [ ] SubTask 5.1: 验证 quotation.pyc 仍然 ok
  - [ ] SubTask 5.2: 批量回归验证 pyc_batch_verify.py batch
  - [ ] SubTask 5.3: 确认至少 1 个 pyc 从 partial 变为 ok
  - [ ] SubTask 5.4: 提交并 push 到远程
- [ ] Task 6: Round 2 - 对下一个最低率 partial pyc 重复 Task 3-5
- [ ] Task 7: 持续迭代 Round 3-10，直到所有 partial pyc 变为 ok 或达到 10 轮

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
