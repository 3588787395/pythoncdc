# R29 测试工程师报告

## 批量验证结果（180/402 文件验证）

| 指标 | 值 |
|------|-----|
| total_pyc | 402 |
| ok_pyc | 222 (55.2%) |
| partial_pyc | 174 (43.3%) |
| failed_pyc | 6 (1.5%) |
| total_functions | 6617 |
| matched_functions | 5380 |
| cumulative_match_rate | 81.31% |

## 剩余 6 个失败文件

| 文件 | 错误类型 | 根因分析 |
|------|----------|----------|
| backtest.pyc | 0% bytecode match (编译通过) | try-except 结构识别错误（PUSH_EXC_INFO vs LOAD_ATTR） |
| strategy_info_utils.pyc | 0% bytecode match (编译通过) | 模块级结构问题 |
| trade_info_utils.pyc | SyntaxError (f-string) | f-string 引号丢失，`""", {expr!s}, """` 应为 `f"""{expr!s}"""` |
| strategy.pyc (plugin_fly_data) | SyntaxError (`s = :10 +`) | 切片表达式 `[:10]` 下界丢失 |
| matcher.pyc | SyntaxError (wildcard) | 重复 `case _:` 通配符（MatchSingleton 退化为 wildcard） |
| pboxAccount_jupyterhub.pyc | SyntaxError (else) | try-except-else 的 else 被放在 if-elif-else 之后 |

## 失败模式分类

1. **Match 模式退化** (matcher.pyc): `case None:` → `case _:`，导致重复通配符
2. **f-string 生成** (trade_info_utils.pyc): 三引号 f-string 被拆分为元组
3. **切片表达式** (strategy.pyc): `keys[:10]` 的 `keys` 部分丢失
4. **try-except-else 结构** (pboxAccount.pyc, backtest.pyc): else 位置错误
5. **模块级结构** (strategy_info_utils.pyc): 函数匹配率为 0%，可能模块级代码结构问题

## R28 修复效果
- 4 个文件从 failed → partial (wizard_quant_api, __init__, function, scheduler)
- 1 个文件从 failed → ok (strategy.pyc in IQCommon/strategy)
- 失败文件从 10+ 降至 6
