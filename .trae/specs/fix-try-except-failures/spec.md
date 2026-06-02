# 修复 try_except 测试失败规范（修订版）

## Why
当前 try_except 区域有8个原始测试失败（通过率 222/230 = 96.5%）。之前的修复尝试引入了6个回归（te10 x3, te25 x3），需要回滚有问题的变更并重新制定修复策略。

## 当前状态

### 基线（原始代码）
8个失败：
1. test_te046.py - with inside try (as variable fb lost)
2. test_te080.py - nested try-except in handler
3. test_te081.py - try-finally with nested try-except
4. test_te100.py - triple nested try
5. test_te104.py - try-except-finally with return
6. test_try15_try_return.py - try with return (SWAP+POP_EXCEPT+RETURN_VALUE)
7. test_try16_multi_nested.py - multi-nested try
8. test_try20_complex_pattern.py - complex pattern

### 当前变更状态
- ✅ te046 已修复（_find_next_with_block 变更无回归）
- ❌ te080/te081/te100/te104/try15/try16/try20 仍失败
- ❌ 新引入6个回归：te10nestedtry_* x3, te25nestedtryexcept_* x3

### 回归根因
1. `inner_handler_indices` 中 PUSH_EXC_INFO 检查（region_analyzer.py 第3895行）导致嵌套 try 的 handler 不被正确标记为 inner handler，使内层 TryExceptRegion 被错误创建
2. `known_handler_starts` 过滤（region_analyzer.py 第4385行）过于激进，过滤掉了合法的异常表条目
3. `_collect_body` 中跳过 TryExceptRegion 块的逻辑（region_analyzer.py 第4763行）导致 handler 体收集不完整
4. `_generate_try` 中嵌套 TryExceptRegion 检测逻辑（region_ast_generator.py 第7177行）将内层 try 错误放入 handler

## What Changes
- **Phase 0**: 回滚有回归的变更，保留 te046 修复
- **Fix A**: te080/te100/try16 — 嵌套 try-except 区域识别与 AST 生成
- **Fix B**: te081 — try-finally 内嵌套 try-except
- **Fix C**: te104 — finally copy 块泄漏到 try body
- **Fix D**: try15 — except handler return 语句
- **Fix E**: try20 — 复杂 try 模式

## Impact
- Affected specs: try_except 区域反编译逻辑
- Affected code: `core/cfg/region_analyzer.py`, `core/cfg/region_ast_generator.py`
- 预期影响: try_except 8f → 0f，无回归

## ADDED Requirements

### Requirement: 嵌套 try-except 正确识别与生成
系统 SHALL 在 region_analyzer 中正确识别嵌套的 TryExceptRegion，并在 region_ast_generator 中正确生成嵌套 try-except AST。

#### Scenario: except handler 内嵌套 try-except (te080)
- **WHEN** 反编译 `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3` 时
- **THEN** 生成正确的嵌套结构：外层 handler body 包含 `try: y = 2 except: z = 3`

#### Scenario: 三层嵌套 try (te100)
- **WHEN** 反编译三层嵌套 try 时
- **THEN** 每层 handler body 包含正确语句，handler 顺序正确

#### Scenario: handler 内嵌套 try-except (try16)
- **WHEN** 反编译多层嵌套 try-except 时
- **THEN** 生成正确的嵌套结构，无语法错误

#### Scenario: 嵌套 try-except 不引入回归 (te10/te25)
- **WHEN** 反编译 `try:\n    try:\n        pass\n    except ValueError:\n        pass\nexcept TypeError:\n        pass` 时
- **THEN** 生成正确的嵌套结构，外层 try body 包含内层 try-except

### Requirement: try-finally 内嵌套 try-except 正确处理 (te081)
系统 SHALL 在 finally body 中正确识别嵌套的 try-except 结构。

#### Scenario: try-finally 内嵌套 try-except
- **WHEN** 反编译 `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3` 时
- **THEN** 生成 `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3`

### Requirement: finally copy 块不泄漏到 try body (te104)
系统 SHALL 在 try-except-finally 模式中，当 except handler 包含 return 语句时，不将 handler return 路径上的 finally copy 块放入 try body。

#### Scenario: try-except-finally-return 正确反编译
- **WHEN** 反编译 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()` 时
- **THEN** try body 不含 `cleanup(); return 'val'`，handler body 包含 `return 'val'`

### Requirement: except handler 中 return 语句正确生成 (try15)
系统 SHALL 在 except handler body 中正确识别 `SWAP; POP_EXCEPT; RETURN_VALUE` 模式为 `return expr`。

#### Scenario: try-return-except-return 正确反编译
- **WHEN** 反编译 `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default` 时
- **THEN** handler body 包含 `return default` 而非 `default; return None`

### Requirement: 复杂 try 模式正确反编译 (try20)
系统 SHALL 在 for 循环内 try-except 中正确处理 continue、raise、多 except handler 和 for-else。

#### Scenario: for-try-except-continue 正确反编译
- **WHEN** 反编译 try20 源码时
- **THEN** 生成正确的结构，不含多余的 `else: return` 和条件反转

### Requirement: with inside try 正确合并 (te046)
系统 SHALL 在 try-except 内正确合并连续的 with 语句。

#### Scenario: with-open-inside-try 正确反编译
- **WHEN** 反编译 `try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()` 时
- **THEN** 生成 `with open('a') as fa, open('b') as fb:`

## MODIFIED Requirements

### Requirement: 回归测试零回归
每次修复后 SHALL 运行 for_loop 回归测试（必须保持 3f）和 if_region 回归测试（必须保持 0f）。如果引入回归，必须立即回滚。

## REMOVED Requirements
（无移除需求）

---

## 详细根因分析与修复策略

### Phase 0: 回滚有回归的变更

需要回滚以下变更：
1. `region_analyzer.py` 第3895行：PUSH_EXC_INFO/WITH_EXCEPT_START 检查（导致 te10/te25 回归）
2. `region_analyzer.py` 第4385行：known_handler_starts 过滤（导致 te10/te25 回归）
3. `region_analyzer.py` 第4763行：_collect_body 中跳过 TryExceptRegion 块（导致 handler 体不完整）
4. `region_analyzer.py` 第4736行：_register_region_blocks 中遍历 region.blocks（可能不需要回滚，需验证）
5. `region_ast_generator.py` 第7177行：_generate_try 中嵌套 TryExceptRegion 检测（导致内层 try 被错误放入 handler）

保留以下变更：
1. `region_analyzer.py` 第5319行：_find_next_with_block 修复（te046 修复，无回归）
2. `region_analyzer.py` 第10653行：chain 排序修复（需验证是否有回归）

### Fix A: te080/te100/try16 — 嵌套 try-except

**根因分析**：
- 对于 `try: x=1 except: try: y=2 except: z=3`，异常表产生6个条目
- 外层 try: [4,8)→12, [12,16)→50
- 内层 try: [18,22)→28, [28,36)→44, [36,38)→50, [44,50)→50
- `_parse_exception_table` 将这些条目合并后，外层 handler_start=12，内层 handler_start=28
- 问题1：`inner_handler_indices` 将内层 handler（offset 28, PUSH_EXC_INFO 开头）错误标记为 inner handler，导致内层 TryExceptRegion 不被创建
- 问题2：即使内层 TryExceptRegion 被创建，其 entry 块（offset 18）在外层 TryExceptRegion 的 try_blocks 中，导致内层 try 被生成在外层 try body 中
- 问题3：`generate` 方法中的 `is_contained` 检查没有处理 TryExceptRegion 嵌套在另一个 TryExceptRegion handler 中的情况

**修复策略**：
1. 在 `_parse_exception_table` 的合并逻辑中，当 `try_start >= handler_start` 时（表示内层 try 在外层 handler 中），需要正确识别这种嵌套关系
2. 在 `generate` 方法的 `is_contained` 检查中，添加 TryExceptRegion 之间的嵌套包含检查：当一个 TryExceptRegion 的 entry 在另一个 TryExceptRegion 的 handler 范围内时，标记为 contained
3. 在 `_generate_try` 方法中，当生成 handler body 时，检测并生成嵌套的 TryExceptRegion

### Fix B: te081 — try-finally 内嵌套 try-except

**根因分析**：
- 对于 `try: x=1 finally: try: y=2 except: z=3`，finally body 中的 try-except 未被识别为嵌套 TryExceptRegion
- finally body 中的块被分散到 try body 和 finalbody 中

**修复策略**：
1. 在 finalbody 生成中，检测 finally_blocks 中属于嵌套 TryExceptRegion 的块
2. 当检测到嵌套 TryExceptRegion 时，调用 `_generate_try` 生成嵌套 try-except 结构

### Fix C: te104 — finally copy 块泄漏

**根因分析**：
- 当 except handler 包含 return 语句时，CPython 会生成 finally copy 块（cleanup + return 'val'）
- 这些块被错误放入 try body

**修复策略**：
1. 在 `_generate_try_body` 中，检测 try_blocks 中的块是否是 finally copy 块
2. 如果某个 try_block 的前驱在 except_handlers 的 blocks 中，则该块是 handler return 路径上的 finally copy 块
3. 将这些块从 try body 中过滤，并加入对应的 handler body

### Fix D: try15 — except handler return 语句

**根因分析**：
- handler body 中 `SWAP; POP_EXCEPT; RETURN_VALUE` 模式未被识别为 `return expr`
- 当前逻辑把 SWAP 之前的 LOAD_GLOBAL 当作独立的 Expr 语句

**修复策略**：
1. 在 handler body 生成中，检测 `LOAD_X; SWAP; POP_EXCEPT; RETURN_VALUE` 模式
2. 生成 `return expr` 而非 `expr; return None`

### Fix E: try20 — 复杂 try 模式

**根因分析**：
- 多个问题叠加：for-else 中多余的 return None、条件判断反转、continue 处理错误
- 可能依赖其他修复（特别是 Fix A 和 Fix D）

**修复策略**：
1. 修复 for-else 中 return None 过滤
2. 修复条件判断逻辑
3. 验证在 Fix A 和 Fix D 完成后是否仍需额外修复
