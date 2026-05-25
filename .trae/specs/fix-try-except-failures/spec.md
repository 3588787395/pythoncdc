# 修复 try_except 11个测试失败规范（Phase 2）

## Why
当前 try_except 区域有11个测试失败（通过率94.9%）。之前的修复已将失败数从21降至11，但剩余问题涉及更复杂的模式：continue→break误识别、多层嵌套try结构、finally copy块泄漏、if-else→IfExp误识别、return语句处理等。需要继续修复 `region_ast_generator.py` 中的AST生成逻辑。

## What Changes
- **Fix A**: continue→break 误识别（te047/te083）— 在 `_try_generate_conditional_break_or_continue` 的 continue+normal 路径中，当 normal 后继的后续块包含 except handler 时，不应设置 `_should_skip_transform`，而应正确生成 `if cond: continue; normal_stmts` 结构
- **Fix B**: 多层嵌套 try 结构（te080/te100/try16）— 改进 `_skipped_outer_try` 机制和 handler 内嵌套 try 的检测
- **Fix C**: Finally copy 块泄漏（te104/te081）— 检测 handler return 路径上的 finally copy 块并正确分配
- **Fix D**: if-else→IfExp 误识别（try11）— 在 try body 中将 TernaryRegion 转换为 If 语句
- **Fix E**: Return 语句处理（try15/try20）— 过滤 try body 中多余的 return None，修复 for-else 中的 return None
- **Fix F**: te050 内层 try-except 在 for 循环中 — 处理 handler body 块与 loop body 块重叠

## Impact
- Affected specs: try_except 区域反编译逻辑
- Affected code: `core/cfg/region_ast_generator.py`（仅此文件）
- 预期影响: try_except 11f → 0f

## ADDED Requirements

### Requirement: try 内 for 循环的 continue 不被误识别为 break
系统 SHALL 在 try 内的 for 循环中，当 `continue` 语句（JUMP_BACKWARD 到循环 header）的后继块包含 except handler 时，不将 `continue` 误识别为 `break`。在 `_try_generate_conditional_break_or_continue` 的 continue+normal 路径中，当 normal 后继的后续块包含 except handler（不在 loop_body_set 中）时，应正确生成 `if cond: continue; normal_stmts` 结构而非 `if cond: break; else: normal_stmts`。

#### Scenario: try-for-continue 正确反编译
- **WHEN** 反编译 `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0` 时
- **THEN** 生成 `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0`

### Requirement: 多层嵌套 try 正确处理
系统 SHALL 在生成嵌套 Try AST 时，正确处理以下模式：
1. except handler 内嵌套 try-except（te080: `try: x=1 except: try: y=2 except: z=3`）
2. 三层嵌套 try（te100: `try: try: try: x=1 except: y=2 except: z=3 except: w=4`）
3. handler 内嵌套 try-except（try16: `try: try: level2() except Error2: try: level3_recover() except Error3: deep_fix() except Error1: top_fix()`）

#### Scenario: except handler 内嵌套 try-except
- **WHEN** 反编译 `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3` 时
- **THEN** 生成正确的嵌套结构，外层 handler body 包含 `try: y = 2 except: z = 3`

### Requirement: finally copy 块不泄漏到 try body
系统 SHALL 在 try-finally 模式中，当 except handler 包含 return 语句时，不将 handler return 路径上的 finally copy 块放入 try body。finally copy 块应仅出现在 finally 子句中。

#### Scenario: try-except-finally-return 正确反编译
- **WHEN** 反编译 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()` 时
- **THEN** 生成 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`

### Requirement: try body 中 if-else 不被识别为 IfExp
系统 SHALL 在 try body 中遇到 TernaryRegion 时，将其转换为 If 语句而非 IfExp 表达式。

#### Scenario: try-if-else-except 正确反编译
- **WHEN** 反编译 `try:\n    if condition:\n        risky()\n    else:\n        safe()\nexcept Error:\n    handle()` 时
- **THEN** 生成 `try:\n    if condition:\n        risky()\n    else:\n        safe()\nexcept Error:\n    handle()`（try body 包含 If 语句而非 IfExp）

### Requirement: try-return-except-return 正确生成
系统 SHALL 在 try-return 模式中：
1. 不在 try body 中生成多余的 `return None`
2. 正确生成 except handler body 中的 return 语句

#### Scenario: try-return-except-return 正确反编译
- **WHEN** 反编译 `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default` 时
- **THEN** 生成 `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default`

## MODIFIED Requirements

### Requirement: 仅修改 region_ast_generator.py
所有修复 SHALL 仅在 `core/cfg/region_ast_generator.py` 中实施，不修改 `region_analyzer.py`。

### Requirement: 回归测试零回归
每次修复后 SHALL 运行完整回归测试（try_except + basic + for_loop + while_loop + if_region），确保其他区域无回归。

## REMOVED Requirements
（无移除需求）

---

## 当前11个失败测试详细根因分析

### Fix A: te047/te083 — continue→break 误识别
- **测试 te047**: `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0`
- **当前输出**: `if i == 1: break; else: x = i`
- **根因**: 在 `_try_generate_conditional_break_or_continue` 的 continue+normal 路径中，block 44（normal 后继，`x = i; JUMP_BACKWARD`）的后继包含 block 54（except handler）。由于 block 54 不在 loop_body_set 中，`_has_post_if_stmts` 被设为 True，导致 `_should_skip_transform = True`。skip transform 路径生成了错误的 If 结构。
- **修复**: 在 `_has_post_if_stmts` 检查中，排除 except handler 块（角色为 EXCEPT_HANDLER 的块）。或者，当 `_should_skip_transform` 为 True 且 continue_succ 存在时，使用 simple_if 路径生成 `if cond: continue; normal_stmts` 结构。

### Fix B1: te080 — except handler 内嵌套 try-except
- **测试**: `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3`
- **当前输出**: `try:\n    try:\n        pass\n    except: y = 2\nexcept: z = 3`（x=1 丢失，结构错误）
- **根因**: region_analyzer 创建了两个 TryExceptRegion：内层（entry=None, try_offset_start=2, try_offset_end=22）和外层（entry=None, try_offset_start=4, try_offset_end=50）。内层是外层的 parent。`_skipped_outer_try` 机制要求 `ntr.try_offset_end > region.try_offset_end`，但内层的 try_offset_end (22) < 外层的 try_offset_end (50)，所以不会被跳过。实际上，内层 try 的 try_blocks 为空，其 handler 包含外层的 handler 块。
- **修复**: 需要改进嵌套 try 检测逻辑，当内层 TryExceptRegion 的 try_blocks 为空时，从外层 region 的 try_blocks 中筛选属于内层 try body 的块。

### Fix B2: te100 — 三层嵌套 try
- **测试**: `try:\n    try:\n        try:\n            x = 1\n        except:\n            y = 2\n    except:\n        z = 3\nexcept:\n    w = 4`
- **当前输出**: `try:\n    try:\n        try:\n            pass\n        except: y = 2\n    except: w = 4\nexcept: z = 3`（x=1 丢失，handler 顺序错误）
- **根因**: 三层嵌套的 region 结构复杂，`_skipped_outer_try` 机制无法正确处理。

### Fix B3: try16 — handler 内嵌套 try-except
- **测试**: `try:\n    try:\n        level2()\n    except Error2:\n        try:\n            level3_recover()\n        except Error3:\n            deep_fix()\nexcept Error1:\n    top_fix()`
- **当前输出**: 语法错误，结构混乱
- **根因**: 三层嵌套 try 的 region 结构复杂，当前的外层 handler 生成逻辑无法正确处理。

### Fix C1: te104 — finally copy 块泄漏到 try body
- **测试**: `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`
- **当前输出**: try body 包含 `x = 1; cleanup(); return 'val'`，handler body 为 `pass`
- **根因**: Block 32（`cleanup(); return 'val'`）是 handler return 路径上的 finally copy 块。它在 try_blocks 中但前驱不在 try_blocks 中（前驱 block 30 在 handler_blocks 中），所以 has_finally 启发式不过滤它。同时 handler body 只包含 POP_EXCEPT 块，不含 return 'val'。
- **修复**: 检测 try_blocks 中的块，如果其前驱在 except_handlers 的 blocks 中，则该块是 handler return 路径上的 finally copy 块，应从 try body 中过滤。

### Fix C2: te081 — try-finally 内嵌套 try-except
- **测试**: `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3`
- **当前输出**: try body 包含 `x = 1; y = 2`，handler 包含 `z = 3`，finalbody 包含 `y = 2; z = 3`
- **根因**: finally 块中的 try-except 子区域未被识别为嵌套 TryExceptRegion，其块被分散到 try body 和 finalbody 中。
- **修复**: 在 finalbody 生成中检测嵌套的 TryExceptRegion 并正确生成。

### Fix D: try11 — if-else 被识别为 IfExp
- **测试**: `try:\n    if condition:\n        risky()\n    else:\n        safe()\nexcept Error:\n    handle()`
- **当前输出**: try body 包含两个重复的 IfExp（三元表达式）
- **根因**: region_analyzer 将 if-else 识别为 TernaryRegion 而非 IfRegion，导致生成 IfExp 而非 If 语句。
- **修复**: 在 try body 中检测 TernaryRegion 并将其转换为 If 语句。

### Fix E1: try15 — try-return except handler body
- **测试**: `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default`
- **当前输出**: try body 包含 `return d[key]; return None`，handler body 包含 `default; return`
- **根因**: try body 中 `return d[key]` 后的隐式 `return None` 块未被过滤。handler body 中 `return default` 被拆分为 `default`（Expr）和 `return`（无值）。
- **修复**: 在 try body 中过滤 `return None` 终端块。在 handler body 中正确识别 return 语句。

### Fix E2: try20 — for-else 多余 return None
- **测试**: `def f():\n    try:\n        for k, v in items:\n            process(k, v)\n    except (TypeError, ValueError):\n        handle_error()`
- **当前输出**: for 循环包含 `else: return None`
- **根因**: for 循环的 else_blocks 包含 block 62（`LOAD_CONST None; RETURN_VALUE`），这是函数的隐式 return None，不应作为 for-else 的内容。
- **修复**: 在 for 循环 else 生成中，过滤 `return None` 块。

### Fix F: te050 — 内层 try-except 在 for 循环中
- **测试**: `try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1`
- **当前输出**: `try:\n    try:\n        for i in range(3):\n            x = 1 / i\n            x = 0\n    except ZeroDivisionError: x = 0\nexcept: x = -1`
- **根因**: 只有一个 TryExceptRegion（外层），内层 try-except 没有被识别为独立的 TryExceptRegion。Block 52（`x = 0`）同时在 LoopRegion 的 body_blocks 和 TryExceptRegion 的 handler_blocks 中。循环先生成了 `x = 0`。
- **修复**: 在循环体生成中，检测属于 TryExceptRegion handler 的块并跳过。
