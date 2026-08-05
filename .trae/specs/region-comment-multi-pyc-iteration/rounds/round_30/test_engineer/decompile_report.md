# R30 测试工程师报告

## 批量验证结果（Python 3.11.7）

| 指标 | R29 | R30 | 变化 |
|------|-----|-----|------|
| total_pyc | 402 | 402 | — |
| ok_pyc | 222 (55.2%) | 222 (55.2%) | — |
| partial_pyc | 174 (43.3%) | 175 (43.5%) | +1 |
| failed_pyc | 6 (1.5%) | 5 (1.2%) | -1 ✓ |
| matched_functions | 5380 | 5391 | +11 |
| cumulative_match_rate | 81.31% | 81.47% | +0.16% |

## R30 修复效果

| 文件 | R29 状态 | R30 状态 | 修复内容 |
|------|----------|----------|----------|
| strategy.pyc (plugin_fly_data) | failed (SyntaxError: `s = :10 +`) | partial (10/24 matched) | ASTSlice 独立表达式 → slice() 调用 |

## 剩余 5 个失败文件

| 文件 | 错误类型 | 根因 |
|------|----------|------|
| backtest.pyc | 0% bytecode match (编译通过) | try-except 结构识别错误 |
| strategy_info_utils.pyc | 0% bytecode match (编译通过) | 模块级结构严重错误 |
| trade_info_utils.pyc | SyntaxError (f-string) | 三引号 f-string 被拆分 |
| matcher.pyc | SyntaxError (wildcard) | 重复 `case _:` 通配符 |
| pboxAccount_jupyterhub.pyc | SyntaxError (else) | try-except-else 结构丢失 |
