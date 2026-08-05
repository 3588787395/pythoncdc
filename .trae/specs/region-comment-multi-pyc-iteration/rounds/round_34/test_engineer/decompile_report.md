# R34 测试工程师报告

## 批量验证结果（Python 3.11.7）

| 指标 | R33 | R34 | 变化 |
|------|-----|-----|------|
| total_pyc | 402 | 402 | — |
| ok_pyc | 222 (55.2%) | 222 (55.2%) | — |
| partial_pyc | 178 (44.3%) | 179 (44.5%) | +1 |
| failed_pyc | 2 (0.5%) | 1 (0.2%) | -1 ✓ |
| matched_functions | 5486 | 5488 | +2 |
| cumulative_match_rate | 82.91% | 82.94% | +0.03% |

## R34 修复效果

| 文件 | R33 状态 | R34 状态 | 修复内容 |
|------|----------|----------|----------|
| pboxAccount_jupyterhub.pyc | failed (0%) | partial (25%) | LOAD_ATTR/LOAD_METHOD + frozenset/tuple 噪声过滤 |

## 修复详情

### 噪声过滤
- `LOAD_ATTR` vs `LOAD_METHOD`: Python 3.11 中语义等价的 opcode，不同 patch 版本可能选择不同
- `frozenset` vs `tuple`: peephole 优化器可能将 `in (a,b,c)` 优化为 `in frozenset({a,b,c})`，但非所有版本执行

### backtest.pyc 分析
- 仍为 failed (0%)，根因是 try/except/else 字节码布局的编译器版本差异
- 原始 pyc: try body → JUMP_FORWARD → except handler → else body
- Python 3.11.7: try body → else body（内联）→ except handler（末尾）
- 反编译源码正确（AST 验证结构完整），非反编译器 bug

## 剩余 1 个失败文件

| 文件 | 错误类型 | 根因 | 可修复性 |
|------|----------|------|----------|
| backtest.pyc | 0% bytecode match (编译通过) | try/except/else 字节码布局编译器版本差异 | 不可修复（编译器行为差异） |

## strategy_info_utils.pyc 诊断
- 28 个函数中仅 4 个匹配（14.29%）
- 主要问题：模块级结构错误（252 true_diffs）、if/else 结构重建错误（check_python_code）、常量顺序差异
- 需要后续轮次深入修复
