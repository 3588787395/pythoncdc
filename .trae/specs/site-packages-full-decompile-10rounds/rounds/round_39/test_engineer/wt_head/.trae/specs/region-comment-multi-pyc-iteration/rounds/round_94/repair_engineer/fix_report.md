# R94 修复工程师报告

## 修复概述

### Pattern: ternary condition_block 中 POP_TOP 终结的表达式语句被丢弃

**缺陷描述**: 当 `_generate_ternary` 处理 TernaryRegion 时，如果 `condition_block` 中包含多条用户语句（如 except handler 中的 `error_info = get_traceback_message()` 和 `system_log.error(f"...")` 调用），`POP_TOP` 终结的表达式语句（如函数调用）不会被提取为 pre_stmts。这导致 `system_log.error(...)` 调用完全丢失。

此外，在 `_generate_try` 中处理嵌套 ternary handler 时，`_generate_ternary` 返回的多语句结果（pre_stmts + ternary assign）中，只有最后一个语句被用于提取 IfExp 作为 exc_type，pre_stmts 被完全丢弃。

**触发条件**: except handler 中使用 try-except 结构，且 except handler body 包含：
1. 赋值语句（如 `error_info = get_traceback_message()`）
2. 表达式语句（如 `system_log.error(f"...")`，以 POP_TOP 终结）
3. 三元表达式赋值（如 `history_data = X if fields is None else X[fields]`）

被 TernaryRegion 识别器将三元表达式所在的 block 作为 condition_block，但该 block 同时包含前面的用户语句。

**修复点1**: `core/cfg/region_ast_generator.py` `_generate_ternary` 方法的 pre_stmts 扫描循环
**修复内容**: 在 `STORE_FAST` 分支之前新增 `POP_TOP` 处理分支：当遇到 `POP_TOP` 且前面有指令时，将前序指令重建为 `Expr` 语句并添加到 pre_stmts，推进 cond_start_idx。

**修复点2**: `core/cfg/region_ast_generator.py` `_generate_try` 方法中嵌套 ternary handler 处理
**修复内容**: 新增 `elif _t_stmts and len(_t_stmts) > 1:` 分支：当 `_generate_ternary` 返回多语句时，从最后一个语句提取 IfExp 作为 exc_type，将前序语句（pre_stmts）添加到 handler_body 前部。

**算法依据**:
- 原则 2（每块唯一归属）：POP_TOP 终结的表达式语句属于独立的 Expr 语句节点，不归属 TernaryRegion 的条件表达式
- 原则 1（自底向上归约）：前驱语句归约为独立 AST 节点，ternary 仅拥有条件 + 值 + merge 块
- 原则 4（父引用子入口）：父 ExceptHandler 通过 ternary 的 IfExp 引用 exc_type，通过 pre_stmts 引用 handler body 前驱语句

## 测试结果
- 最小复现实例: PASS（log.error 调用存在，error_info 赋值存在）
- quotation.pyc: 143/143 (100%)，无回归
- klinedata.pyc: 31/45 (68.9%)，+4 匹配函数（27->31）
- 批量验证: 265 OK, 137 partial, 0 failed, 91.29% (6040/6616)，+4 匹配函数

## 修复影响的函数
- `get_kline_by_date_one`: `system_log.error(...)` 调用恢复
- `get_kline_by_date_new`: `system_log.error(...)` 调用恢复
- `get_kline_by_count`: `system_log.error(...)` 调用恢复
- `get_kline_by_count_new`: `system_log.error(...)` 调用恢复
