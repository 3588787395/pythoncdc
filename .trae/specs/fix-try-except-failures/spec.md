# 修复 try_except 10个测试失败规范

## Why
当前 try_except 区域有10个测试失败（通过率 209/230 = 90.9%）。失败涉及4种模式：for-try-continue→break误识别、嵌套try结构无法识别、try-finally内嵌套try/return语句处理错误、复杂try模式。需要修复 `region_analyzer.py` 和 `region_ast_generator.py` 中的逻辑。

## What Changes
- **Fix A**: for-try-continue→break 误识别（te047/te083/te050）— 在 `_try_generate_conditional_break_or_continue` 中，当 fall_through 后继是异常处理入口块（PUSH_EXC_INFO/WITH_EXCEPT_START）时，跳过该后继选择真正的 fall_through 块
- **Fix B**: 嵌套 try 结构（te080/te100/try16）— 在 `_parse_exception_table` 中，当 `try_start >= handler_start` 时向后搜索实际的 try body 起始位置；在 `_find_actual_handler_start` 中添加 bare except 检测和候选者选择逻辑
- **Fix C**: try-finally 内嵌套 try / return 处理（te081/te104/try15）— 在 finally body 生成中检测嵌套 TryExceptRegion；过滤 finally copy 块从 try body；修复 handler body 中 return 语句生成
- **Fix D**: 复杂 try 模式（try20）— 修复 for-else 中多余的 return None，修复条件反转

## Impact
- Affected specs: try_except 区域反编译逻辑
- Affected code: `core/cfg/region_analyzer.py`, `core/cfg/region_ast_generator.py`
- 预期影响: try_except 10f → 0f

## ADDED Requirements

### Requirement: try 内 for 循环的 continue 不被误识别为 break
系统 SHALL 在 try 内的 for 循环中，当 `continue` 语句的后继块包含异常处理入口（PUSH_EXC_INFO/WITH_EXCEPT_START）时，不将该后继作为 fall_through，而应选择真正的 fall_through 块。

#### Scenario: try-for-continue 正确反编译 (te047)
- **WHEN** 反编译 `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0` 时
- **THEN** 生成 `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0`

#### Scenario: try-for-continue 正确反编译 (te083)
- **WHEN** 反编译 `try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1` 时
- **THEN** 生成 `try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1`

### Requirement: for 循环内嵌套 try-except 正确识别 (te050)
系统 SHALL 在 for 循环体内正确识别嵌套的 try-except 结构，不将 except handler 的语句混入循环体。

#### Scenario: for-try-except 正确反编译
- **WHEN** 反编译 `try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1` 时
- **THEN** 循环体包含嵌套 try-except，`x = 0` 仅出现在 except handler 中

### Requirement: 嵌套 try-except 正确处理
系统 SHALL 在生成嵌套 Try AST 时，正确处理以下模式：
1. except handler 内嵌套 try-except（te080: `try: x=1 except: try: y=2 except: z=3`）
2. 三层嵌套 try（te100: `try: try: try: x=1 except: y=2 except: z=3 except: w=4`）
3. handler 内嵌套 try-except（try16: `try: try: level2() except Error2: try: level3_recover() except Error3: deep_fix() except Error1: top_fix()`）

#### Scenario: except handler 内嵌套 try-except (te080)
- **WHEN** 反编译 `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3` 时
- **THEN** 生成正确的嵌套结构，外层 handler body 包含 `try: y = 2 except: z = 3`

#### Scenario: 三层嵌套 try (te100)
- **WHEN** 反编译三层嵌套 try 时
- **THEN** 每层 handler body 包含正确的语句，handler 顺序正确

#### Scenario: handler 内嵌套 try-except (try16)
- **WHEN** 反编译多层嵌套 try-except 时
- **THEN** 生成正确的嵌套结构，无语法错误

### Requirement: try-finally 内嵌套 try-except 正确处理 (te081)
系统 SHALL 在 finally body 中正确识别嵌套的 try-except 结构。

#### Scenario: try-finally 内嵌套 try-except
- **WHEN** 反编译 `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3` 时
- **THEN** 生成 `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3`

### Requirement: finally copy 块不泄漏到 try body (te104)
系统 SHALL 在 try-except-finally 模式中，当 except handler 包含 return 语句时，不将 handler return 路径上的 finally copy 块放入 try body。

#### Scenario: try-except-finally-return 正确反编译
- **WHEN** 反编译 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()` 时
- **THEN** 生成 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`

### Requirement: except handler 中 return 语句正确生成 (try15)
系统 SHALL 在 except handler body 中正确识别 `SWAP; POP_EXCEPT; RETURN_VALUE` 模式为 `return expr`，而非拆分为 `expr; return None`。

#### Scenario: try-return-except-return 正确反编译
- **WHEN** 反编译 `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default` 时
- **THEN** 生成 `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default`

### Requirement: 复杂 try 模式正确反编译 (try20)
系统 SHALL 在 for 循环内 try-except 中正确处理 continue、raise、多 except handler 和 for-else。

#### Scenario: for-try-except-continue 正确反编译
- **WHEN** 反编译 try20 源码时
- **THEN** 生成正确的结构，不含多余的 `else: return` 和条件反转

## MODIFIED Requirements

### Requirement: 回归测试零回归
每次修复后 SHALL 运行完整回归测试（try_except），确保其他测试无回归。如果回归超过5个，必须回滚。

## REMOVED Requirements
（无移除需求）

---

## 10个失败测试详细根因分析

### Fix A1: te047 — continue→break 误识别
- **测试**: `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0`
- **当前输出**: `if i == 1: break; i`（continue 被误识别为 break，x=i 变成了 i）
- **根因**: 在 `_try_generate_conditional_break_or_continue` 中，block 的两个后继是 loop header（continue target）和 except handler 入口（PUSH_EXC_INFO）。fall_through 选择时把 except handler 入口当作 fall_through，导致 continue 被误判为 break。
- **修复**: 在选择 fall_through 时，跳过包含 PUSH_EXC_INFO/WITH_EXCEPT_START 的后继块。

### Fix A2: te083 — continue→break 误识别
- **测试**: `try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1`
- **当前输出**: `if i < 1: break; continue`（continue 被误识别为 break）
- **根因**: 同 te047
- **修复**: 同 te047

### Fix A3: te050 — 内层 try-except 未识别
- **测试**: `try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1`
- **当前输出**: `try:\n    try:\n        for i in range(3):\n            x = 1 / i\n            x = 0\n    except ZeroDivisionError:\n        x = 0\nexcept:\n    x = -1`
- **根因**: 内层 try-except 的 handler 块（x=0）被混入循环体。可能需要修改 `_find_actual_handler_start` 添加 bare except 检测，或在循环体生成中跳过属于 TryExceptRegion handler 的块。
- **修复**: 需要进一步分析，可能涉及 region_analyzer 中内层 try 的识别和 ast_generator 中循环体生成时对 handler 块的过滤。

### Fix B1: te080 — except handler 内嵌套 try-except
- **测试**: `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3`
- **当前输出**: `pass`（完全失败，TRY_EXCEPT 未找到）
- **根因**: 内层 try-except 的异常表条目 try_start >= handler_start，region_analyzer 无法正确创建 TryExceptRegion。需要向后搜索实际的 try body 起始位置。
- **修复**: 在 `_parse_exception_table` 中，当 `try_start >= handler_start` 时，向后搜索实际的 try body 起始位置。在 `_find_actual_handler_start` 中添加 bare except 检测。

### Fix B2: te100 — 三层嵌套 try handler 顺序错误
- **测试**: `try:\n    try:\n        try:\n            x = 1\n        except:\n            y = 2\n    except:\n        z = 3\nexcept:\n    w = 4`
- **当前输出**: handler 顺序错误（z=3 和 w=4 互换）
- **根因**: 嵌套 try 的异常表条目合并时 try_end 计算错误，导致 handler 分配错误。
- **修复**: 修复异常表条目合并逻辑，确保 try_end 不超过 handler_start。

### Fix B3: try16 — 多层嵌套 try 完全失败
- **测试**: `try:\n    try:\n        level2()\n    except Error2:\n        try:\n            level3_recover()\n        except Error3:\n            deep_fix()\nexcept Error1:\n    top_fix()`
- **当前输出**: `pass`（完全失败）
- **根因**: 同 te080，嵌套 try-except 的异常表条目无法正确解析。
- **修复**: 同 te080

### Fix C1: te081 — try-finally 内嵌套 try-except
- **测试**: `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3`
- **当前输出**: try body 包含 `x=1; y=2`，except 包含 `z=3`，finally 包含 `y=2; z=3`
- **根因**: finally body 中的 try-except 未被识别为嵌套 TryExceptRegion，其块被分散到 try body 和 finalbody 中。
- **修复**: 在 finalbody 生成中检测嵌套的 TryExceptRegion 并正确生成。

### Fix C2: te104 — finally copy 块泄漏到 try body
- **测试**: `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`
- **当前输出**: try body 包含 `x=1; cleanup(); return 'val'`，handler body 为 `pass`
- **根因**: Block（cleanup + return 'val'）是 handler return 路径上的 finally copy 块，被错误放入 try body。
- **修复**: 检测 try_blocks 中的块，如果其前驱在 except_handlers 的 blocks 中，则该块是 handler return 路径上的 finally copy 块，应从 try body 中过滤并加入 handler body。

### Fix C3: try15 — except handler return 语句错误
- **测试**: `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default`
- **当前输出**: handler body 包含 `default; return None` 而非 `return default`
- **根因**: handler body 生成中，`SWAP; POP_EXCEPT; RETURN_VALUE` 模式未被识别为 `return expr`。`SWAP` 把 default 值放到栈顶，`POP_EXCEPT` 清理异常，`RETURN_VALUE` 返回 default。当前逻辑把 SWAP 之前的 LOAD_GLOBAL 当作独立的 Expr 语句，return 时栈上已无值。
- **修复**: 在 handler body 生成中，检测 `LOAD_X; SWAP; POP_EXCEPT; RETURN_VALUE` 模式并生成 `return expr`。

### Fix D: try20 — 复杂 try 模式
- **测试**: 复杂 for-try-except-continue 模式
- **当前输出**: 条件反转、if-else 结构错误、多余的 `else: return`
- **根因**: 多个问题叠加：for-else 中多余的 return None、条件判断反转、continue 处理错误。
- **修复**: 修复 for-else 中 return None 过滤、条件判断逻辑。
