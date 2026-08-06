# R40 Spec Round — Dict Comprehension Key 表达式方法调用修复

## 修复概述

### Fix: _find_dict_kv_split_point 栈深度计算错误（comprehension_generator.py）
- **问题**: `_get_stack_delta` 对 `CALL n` 返回 `-(n)+1`，未考虑 Python 3.11
  `LOAD_METHOD` 调用约定中的 NULL 标记。`LOAD_METHOD` 压入 NULL+method（delta +1），
  `CALL n` 需弹出 n+2（n 参数 + callable + NULL）并压入 1 结果，正确 delta = -(n+1)。
  原代码 delta = -(n)+1 = 0（对 CALL 1），导致栈深度追踪错误：
  - `value.strftime('%Y-%m-%d')` 的栈深度应为 0→1→2→3→3→1（CALL 后回到 1），
    但错误计算为 0→1→2→3→3→3（CALL 后仍为 3）。
  - Key/value 分割点检测失败，method call 被丢弃，
    `{value.strftime('%Y-%m-%d'): key}` 变为 `{value: key}`。
- **修复**: 在 `_find_dict_kv_split_point` 中跟踪 `LOAD_METHOD` 调用约定，
  当 `CALL` 前有 `LOAD_METHOD` 时使用 delta = -(n+1)，否则使用 delta = -n。
- **影响文件**: `tradingday_calendar.pyc` 的 `<dictcomp>` 字节码完全匹配。

## 验证结果
- 修复前: `{value.strftime('%Y-%m-%d'): key}` 被反编译为 `{value: key}`（6 true_diffs）
- 修复后: `{value.strftime('%Y-%m-%d'): key}` 字节码完全匹配（0 diffs）

## 方法注释模板 (6/4 节)
### comprehension_generator.py - _find_dict_kv_split_point 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R40 修复 dict comprehension key 表达式含方法调用时
    key/value 分割点检测失败的问题。根因是 _get_stack_delta 对 CALL 指令的
    栈深度计算未考虑 LOAD_METHOD 的 NULL 调用约定。
  - 后 4 行（技术依据）: 区域归约算法原则 2（每块唯一归属）—— dict comp 的
    key_expr 和 value_expr 是 MAP_ADD 的两个子节点，分割点是它们之间的边界。
    栈深度追踪必须精确反映 Python 3.11 CALL 调用约定的实际栈效应，
    否则分割点错误导致 key 表达式的方法调用部分丢失。
