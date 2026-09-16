# Tasks

## Round 1
- [ ] Task 1: Test Engineer - 对39个partial pyc按字节码匹配率从低到高排序，取最低的pyc文件进行详细分析
  - [ ] SubTask 1.1: 对function.pyc(73.33%)执行single验证，获取mismatch详情
  - [ ] SubTask 1.2: 分析4个mismatch函数的字节码差异，归类区域模式
  - [ ] SubTask 1.3: 为每个mismatch函数创建最小复现实例（10+个）
  - [ ] SubTask 1.4: 将分析结果整理为修复工程师可用的报告
- [ ] Task 2: Fix Engineer - 根据测试工程师报告，完善region_analyzer.py和region_ast_generator.py
  - [ ] SubTask 2.1: 针对每个区域模式，在识别方法中写入反编译逻辑注释
  - [ ] SubTask 2.2: 实现修复代码
  - [ ] SubTask 2.3: 用quotation.pyc验证修复不引入回归
  - [ ] SubTask 2.4: 用pyc_batch_verify.py执行批量回归验证
- [ ] Task 3: Round 1 完成验证 - 确认至少1个pyc从partial变为ok
  - [ ] SubTask 3.1: 执行batch验证统计成功率
  - [ ] SubTask 3.2: git commit并push

## Round 2-10 (每轮相同结构)
- [ ] Task N*3-2: Test Engineer - 取下一个最低匹配率pyc分析
- [ ] Task N*3-1: Fix Engineer - 修复
- [ ] Task N*3: Round验证 + commit + push

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Each round depends on previous round completion
