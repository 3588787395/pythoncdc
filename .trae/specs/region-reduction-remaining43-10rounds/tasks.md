# Tasks

## Task 0：基线重建（已完成）
- [x] SubTask 0.1: 确认 pyc 目标版本 = Python 3.11（magic 3495），解释器中 `D:/Python/python.exe` (3.11.7)
- [x] SubTask 0.2: 用正确解释器全量复测 402 pyc，生成 `baseline_index.json`

## Round 01
- [ ] SubTask 1.1: 测试工程师：分析 `trade_info_utils.pyc`（40 函数 / 32 匹配）字节码差异，产出 10+ 最小复现实例
- [ ] SubTask 1.2: 修复工程师：按区域归约算法完善识别逻辑，识别方法写入反编译逻辑注释
- [ ] SubTask 1.3: 验证 quotation.pyc
- [ ] SubTask 1.4: `scripts/pyc_batch_verify.py` 批量回归（不引入回归）
- [ ] SubTask 1.5: git commit + push

## Round 02
- [ ] SubTask 2.1: 测试工程师分析下一个最低匹配率 pyc，产出 10+ 复现实例
- [ ] SubTask 2.2: 修复工程师完善代码 + 注释
- [ ] SubTask 2.3: quotation 验证 + 批量回归 + 提交 push

## Round 03
- [ ] SubTask 3.1: 测试工程师分析
- [ ] SubTask 3.2: 修复工程师完善
- [ ] SubTask 3.3: quotation 验证 + 批量回归 + 提交 push

## Round 04
- [ ] SubTask 4.1: 测试工程师分析
- [ ] SubTask 4.2: 修复工程师完善
- [ ] SubTask 4.3: quotation 验证 + 批量回归 + 提交 push

## Round 05
- [ ] SubTask 5.1: 测试工程师分析
- [ ] SubTask 5.2: 修复工程师完善
- [ ] SubTask 5.3: quotation 验证 + 批量回归 + 提交 push

## Round 06
- [ ] SubTask 6.1: 测试工程师分析
- [ ] SubTask 6.2: 修复工程师完善
- [ ] SubTask 6.3: quotation 验证 + 批量回归 + 提交 push

## Round 07
- [ ] SubTask 7.1: 测试工程师分析
- [ ] SubTask 7.2: 修复工程师完善
- [ ] SubTask 7.3: quotation 验证 + 批量回归 + 提交 push

## Round 08
- [ ] SubTask 8.1: 测试工程师分析
- [ ] SubTask 8.2: 修复工程师完善
- [ ] SubTask 8.3: quotation 验证 + 批量回归 + 提交 push

## Round 09
- [ ] SubTask 9.1: 测试工程师分析
- [ ] SubTask 9.2: 修复工程师完善
- [ ] SubTask 9.3: quotation 验证 + 批量回归 + 提交 push

## Round 10
- [ ] SubTask 10.1: 测试工程师分析
- [ ] SubTask 10.2: 修复工程师完善
- [ ] SubTask 10.3: quotation 验证 + 批量回归 + 提交 push

# Task Dependencies
- Round N 依赖 Round N-1（顺序执行，每轮必须先解决 ≥1 个 pyc）
- 每轮 Round 的 SubTask .3 依赖 .1 与 .2
