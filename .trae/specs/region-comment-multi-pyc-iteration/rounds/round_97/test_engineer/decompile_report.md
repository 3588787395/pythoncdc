# R97 测试工程师报告：function.pyc + 全局模式分析

## 概述

- **分析目标**：全局 partial pyc 模式分析 + function.pyc 深度分析
- **轮次**：R97
- **全局累计成功率**：91.38%（与 R96 持平）
- **全局 OK pyc 数**：266

## 全局模式分析

对前 40 个 partial pyc 文件的所有不匹配函数进行模式统计：
- `other`（语句顺序错位）：16333 个 diff
- `LOAD_CONST_None_vs_something`（多余 return None 相关）：368 个 diff
- `JUMP_FORWARD_missing`（JUMP_FORWARD 被丢失）：39 个 diff
- `POP_TOP_vs_RETURN_VALUE`（POP_TOP 被误判为 RETURN_VALUE）：15 个 diff

结论：绝大多数 diff（16333/16755 = 97.5%）是语句顺序错位，根因是反编译器控制流区域识别错误。

## function.pyc 分析

- **路径**：`site-packages/IQEngine/plugins/plugin_system_trade/function.pyc`
- **匹配率**：85.92%（61/71 函数匹配）
- **不匹配函数**：10 个

### 不匹配函数模式

| 函数名 | true_diffs | 模式 |
|--------|-----------|------|
| cancel_order_ex_handle | 154 | JUMP_FORWARD 后代码错位 |
| cb_order_flag_handle | 31 | 语句顺序错位 |
| debt_to_stock_order_handle | 143 | return 后语句错位 |
| entrust_list_query | 145 | if 分支体错位 |
| future_position_data_position_handle | 93 | POP_TOP 误判为 RETURN_VALUE |
| get_entrust_item_info | 366 | JUMP_FORWARD 后代码错位 |
| order_entrust_info_handle | 124 | 语句顺序错位 |
| position_list_query | 145 | if 分支体错位 |
| read_order_from_csv | 108 | JUMP_FORWARD 后代码错位 |
| reconnect | 46 | 语句顺序错位 |

## 最小复现实例

10 个最小复现实例已归档至 `minimal_repros/`。
