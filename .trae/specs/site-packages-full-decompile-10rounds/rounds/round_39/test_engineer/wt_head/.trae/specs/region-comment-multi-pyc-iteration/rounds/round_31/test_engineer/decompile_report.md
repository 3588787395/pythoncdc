# R31 测试工程师报告

## 批量验证结果（Python 3.11.7）

| 指标 | R30 | R31 | 变化 |
|------|-----|-----|------|
| total_pyc | 402 | 402 | — |
| ok_pyc | 222 (55.2%) | 222 (55.2%) | — |
| partial_pyc | 175 (43.5%) | 176 (43.8%) | +1 |
| failed_pyc | 5 (1.2%) | 4 (1.0%) | -1 ✓ |
| matched_functions | 5391 | 5397 | +6 |
| cumulative_match_rate | 81.47% | 81.56% | +0.09% |

## R31 修复效果

| 文件 | R30 状态 | R31 状态 | 修复内容 |
|------|----------|----------|----------|
| matcher.pyc | failed (SyntaxError: wildcard) | partial 88.24% (15/17) | 重复 case _ 通配符去重 |
| trade_info_utils.pyc | failed (SyntaxError: f-string) | partial 47.50% (19/40) | ''.join([...]) → f-string 转换 |

## 剩余 4 个失败文件

| 文件 | 错误类型 | 根因 | 修复难度 |
|------|----------|------|----------|
| backtest.pyc | 0% bytecode match (编译通过) | try-except 范围不正确 | 中 |
| strategy_info_utils.pyc | 0% bytecode match (编译通过) | 模块级结构错误 | 中 |
| pboxAccount_jupyterhub.pyc | SyntaxError (else) | if-else then_blocks 过度收集 | 高 |
| matcher.pyc | partial 88.24% | 2 个函数不匹配 | 低 |
