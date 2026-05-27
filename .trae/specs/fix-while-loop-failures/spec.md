# while_loop 5个失败测试修复 Spec

## Why
while_loop区域当前5f/102p(95.3%)，剩余5个失败测试涉及4种不同根因：else块return None丢失、嵌套while条件块重复生成、多break场景else:continue误生成、elif链断裂。修复后目标0f(100%)。

## What Changes
- 修复 `_loop_generate_while` 中 `_else_return_none_as_post` 逻辑：当while的else块仅含return None时，将其作为while后置语句而非else子句
- 修复 `_loop_generate_while` 中 `_cond_was_generated` 处理：当条件块已被外层循环生成时，跳过整个条件块指令迭代，避免重复pre_stmts
- 修复 `_try_generate_conditional_break_or_continue` 中else后继为continue时的误生成：当else后继是循环回边块且含有效指令时，不生成`else: continue`
- 修复 while20 elif链断裂：确保循环体内IfRegion的elif链正确生成

## Impact
- Affected code: `core/cfg/region_ast_generator.py` (唯一修改文件)
- Affected tests: `tests/exhaustive/while_loop/` 下5个失败测试
- Regression guard: basic必须0f, for_loop必须≤7f

## ADDED Requirements

### Requirement: while13 — else块return None保留
系统 SHALL 在while循环的else块仅含`return None`时，将`return None`作为while循环后的独立语句生成，而非作为else子句内容或完全丢失。

#### Scenario: while13_while_return
- **WHEN** 反编译 `def find_match(items):\n    while items:\n        item = items.pop()\n        if matches(item):\n            return item\n    return None` 时
- **THEN** 生成 `while items: ... \nreturn None`（return None在while之后，非else子句）

### Requirement: while15 — 嵌套while条件块不重复生成
系统 SHALL 当内层while循环的条件块已被外层循环的`_loop_handle_header`生成时，内层while的`_loop_generate_while`不再重复生成该条件块的pre_stmts。

#### Scenario: while15_nested_while
- **WHEN** 反编译 `while rows:\n    row = rows.pop(0)\n    cols = list(row)\n    while cols:\n        val = cols.pop(0)\n        process(val)` 时
- **THEN** `row = rows.pop(0)` 和 `cols = list(row)` 各只出现一次

### Requirement: wl32 — 多break场景不误生成else:continue
系统 SHALL 当if-break的else后继是循环回边块（含有效指令如`n += 1`）时，不生成`else: continue`，而是让代码自然落入后续语句。

#### Scenario: wl32whilemultibreak
- **WHEN** 反编译 `n = 0\nwhile n < 100:\n    if n == 3: break\n    if n == 7: break\n    n += 1` 时
- **THEN** 生成 `if n == 3: break\nif n == 7: break\nn += 1`（无`else: continue`）

### Requirement: while20 — elif链正确生成
系统 SHALL 在while循环体内正确生成if/elif/else链，不将elif分支断裂为独立语句。

#### Scenario: while20_complex_state_machine
- **WHEN** 反编译含if/elif/else链的while循环时
- **THEN** elif分支作为if语句的orelse子句生成，而非独立表达式语句

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）

## 根因分析

### while13: return None丢失
- **现象**: 反编译输出缺少`return None`
- **根因**: `_else_return_none_as_post`逻辑在`has_trailing_return_none=True`且else_stmts全为trailing return None时，清空else_stmts并设置flag，但flag添加return None的逻辑可能未正确触发。需要检查while13的while循环是否在函数体内被嵌套处理（作为code object），导致return None的生成路径不同。

### while15: 重复pre_stmts
- **现象**: `row = rows.pop(0)` 和 `cols = list(row)` 各出现两次
- **根因**: 外层while的`_loop_handle_header`已生成条件块的pre_stmts和内层while，但内层while的`_loop_generate_while`再次遍历条件块指令生成pre_stmts。`_cond_was_generated`检查(line 1967)仅在pre_stmts为空时清空，但for循环已执行并积累了语句。

### wl32: else:continue误生成
- **现象**: `if n == 7: break\nelse: continue` 而非 `if n == 7: break`
- **根因**: `_try_generate_conditional_break_or_continue`在处理if-break时，else后继是循环回边块，被识别为continue目标，生成了`else: continue`。但回边块含有效指令(`n += 1`)，不应被当作纯continue处理。

### while20: elif链断裂
- **现象**: `state == 'processing'\ncontinue` 而非 `elif state == 'processing':`
- **根因**: 循环体内的IfRegion elif链在`_process_if_blocks`或`_loop_dispatch_block`中被错误处理，elif分支被当作独立块生成而非if的orelse子句。
