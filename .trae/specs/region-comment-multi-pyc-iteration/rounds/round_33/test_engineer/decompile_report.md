# R33 测试工程师报告

## 批量验证结果（Python 3.11.7）

| 指标 | R32 | R33 | 变化 |
|------|-----|-----|------|
| total_pyc | 402 | 402 | — |
| ok_pyc | 222 (55.2%) | 222 (55.2%) | — |
| partial_pyc | 177 (44.0%) | 178 (44.3%) | +1 |
| failed_pyc | 3 (0.7%) | 2 (0.5%) | -1 ✓ |
| matched_functions | 5420 | 5486 | +66 |
| cumulative_match_rate | 81.91% | 82.91% | +1.00% |

## R33 修复效果

| 文件 | R32 状态 | R33 状态 | 修复内容 |
|------|----------|----------|----------|
| bar.pyc (IQEngine/core) | partial, 1.72% | partial, 81.03% | _generate_remaining_stmts 委托 _build_store_statement |

## 修复详情

### bar.pyc (IQEngine/core)
- **R32 匹配率**: 1.72%（仅 1-2 个函数匹配）
- **R33 匹配率**: 81.03%（47/58 函数匹配）
- **根因**: 模块级代码包含推导式后跟类定义（`BarData`/`TickBar`/`BarDict`）。推导式生成器 `ComprehensionGenerator._generate_remaining_stmts` 处理推导式后的剩余指令时，直接用 `expr_reconstructor.reconstruct + Assign` 构造语句，跳过了 `ClassDef` 识别逻辑
- **修复后**: 三个类定义正确生成为 `class BarData(object):` / `class TickBar(object):` / `class BarDict(object):`
- **剩余 11 个不匹配函数**: `<module>`(127 diffs), `BarData`(133 diffs, property 相关), `__getitem__`(64 diffs), `__repr__`(26 diffs) 等

## 第二个 bar.pyc (local_variables)
- 匹配率: 95.45%（21/22 函数匹配），与 R32 一致，无回归 ✓

## 剩余 2 个失败文件

| 文件 | 错误类型 | 根因 | 修复难度 |
|------|----------|------|----------|
| backtest.pyc | 0% bytecode match (编译通过) | try-except 范围不正确 | 中 |
| strategy_info_utils.pyc | 0% bytecode match (编译通过) | 模块级结构错误 | 中 |
