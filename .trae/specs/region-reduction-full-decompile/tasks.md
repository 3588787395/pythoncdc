# Tasks

- [ ] Task 1: 建立待修复 pyc 索引队列
  - [ ] SubTask 1.1: 从 pyc_index.json 读取所有 decompile_status != 'ok' 的条目
  - [ ] SubTask 1.2: 按 bytecode_match_rate 升序排列，形成优先级队列
  - [ ] SubTask 1.3: 输出队列摘要（43 个文件，最低 rate 到最高 rate）

- [ ] Task 2: 第1轮迭代 - 修复 history_api.pyc (rate=0.5556, 最低)
  - [ ] SubTask 2.1: 测试工程师对 history_api.pyc 执行 pyc_batch_verify.py single，收集 mismatches 详情
  - [ ] SubTask 2.2: 测试工程师分析每个 mismatch 函数的 first_diff，归类模式
  - [ ] SubTask 2.3: 测试工程师创建最小复现实例（10+个可复现问题的 .py 文件）
  - [ ] SubTask 2.4: 修复工程师根据分析修改 region_analyzer.py / region_ast_generator.py
  - [ ] SubTask 2.5: 验证 history_api.pyc 的 bytecode_match_rate 达到 1.0
  - [ ] SubTask 2.6: 批量回归验证已 ok 的 pyc
  - [ ] SubTask 2.7: 提交并 push

- [ ] Task 3: 第2轮迭代 - 修复 klinedata.pyc (rate=0.6)
  - [ ] SubTask 3.1: 测试工程师分析 klinedata.pyc mismatches
  - [ ] SubTask 3.2: 创建最小复现实例
  - [ ] SubTask 3.3: 修复工程师完善代码
  - [ ] SubTask 3.4: 验证 rate 达到 1.0
  - [ ] SubTask 3.5: 批量回归验证
  - [ ] SubTask 3.6: 提交并 push

- [ ] Task 4: 第3轮迭代 - 修复 finance.pyc (rate=0.6667)
  - [ ] SubTask 4.1: 测试分析 + 最小复现实例
  - [ ] SubTask 4.2: 修复代码
  - [ ] SubTask 4.3: 验证 + 回归 + 提交 push

- [ ] Task 5: 第4轮迭代 - 修复 replace_utils.pyc (rate=0.6667)
  - [ ] SubTask 5.1: 测试分析 + 最小复现实例
  - [ ] SubTask 5.2: 修复代码
  - [ ] SubTask 5.3: 验证 + 回归 + 提交 push

- [ ] Task 6: 第5轮迭代 - 修复 function.pyc (rate=0.6667)
  - [ ] SubTask 6.1: 测试分析 + 最小复现实例
  - [ ] SubTask 6.2: 修复代码
  - [ ] SubTask 6.3: 验证 + 回归 + 提交 push

- [ ] Task 7: 第6轮迭代 - 修复 trade_info_utils.pyc (rate=0.7)
  - [ ] SubTask 7.1: 测试分析 + 最小复现实例
  - [ ] SubTask 7.2: 修复代码
  - [ ] SubTask 7.3: 验证 + 回归 + 提交 push

- [ ] Task 8: 第7轮迭代 - 修复 quote.pyc (rate=0.716)
  - [ ] SubTask 8.1: 测试分析 + 最小复现实例
  - [ ] SubTask 8.2: 修复代码
  - [ ] SubTask 8.3: 验证 + 回归 + 提交 push

- [ ] Task 9: 第8轮迭代 - 修复 real_quote.pyc (rate=0.7273)
  - [ ] SubTask 9.1: 测试分析 + 最小复现实例
  - [ ] SubTask 9.2: 修复代码
  - [ ] SubTask 9.3: 验证 + 回归 + 提交 push

- [ ] Task 10: 第9轮迭代 - 修复 finance_data_source.pyc (rate=0.7778)
  - [ ] SubTask 10.1: 测试分析 + 最小复现实例
  - [ ] SubTask 10.2: 修复代码
  - [ ] SubTask 10.3: 验证 + 回归 + 提交 push

- [ ] Task 11: 第10轮迭代 - 修复 trade_live_broker.pyc (rate=0.7815)
  - [ ] SubTask 11.1: 测试分析 + 最小复现实例
  - [ ] SubTask 11.2: 修复代码
  - [ ] SubTask 11.3: 验证 + 回归 + 提交 push

- [ ] Task 12: 后续轮次 - 继续修复剩余 33 个 pyc 文件（从 rate=0.7895 到 rate=0.9583）
  - [ ] SubTask 12.1: 逐个按优先级修复
  - [ ] SubTask 12.2: 每轮验证 + 回归 + 提交 push

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
- Task 8 depends on Task 7
- Task 9 depends on Task 8
- Task 10 depends on Task 9
- Task 11 depends on Task 10
- Task 12 depends on Task 11
