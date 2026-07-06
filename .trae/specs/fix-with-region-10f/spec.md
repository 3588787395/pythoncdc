# 修复 with_region 10 个测试失败规范

## Why
当前反编译器在 with_region 有 10 个测试失败（基线 76f/1734p, 95.8%）。这些失败涉及 4 种模式：with+boolop 重复指令、with+try 异常处理错误、with+loop 嵌套指令不匹配、with+custom context 指令偏多。需要增量修复这些失败，同时确保全量回归测试不超过 5f 阈值。

## What Changes
- **修复 Pattern A (w035/w043)**: with body 中 BoolOpRegion/LoopRegion 块的重复 prefix 指令生成
- **修复 Pattern B (w045)**: with+try/except/else 中 TryExceptRegion 的 else_blocks 错误识别（with cleanup 块被误认为 else 块）
- **修复 Pattern C (w058/w079/w080)**: with+try 嵌套中异常处理区域与 with 自身异常处理的冲突
- **修复 Pattern D (w099/w100/w102)**: with+loop 嵌套中循环子区域处理
- **修复 Pattern E (w30withcustomctx)**: with+custom context 中 class 定义块生成顺序
- **修复 generate() 顶层**: 跳过代表 with 语句自身异常处理的 TryExceptRegion，避免生成 `try:...except:pass except:pass` 无效语法
- 主要修改 `core/cfg/region_ast_generator.py`，必要时修改 `core/cfg/region_analyzer.py`

## Impact
- Affected code: `core/cfg/region_ast_generator.py`（_generate_with, generate, _fix_try_else_in_with 等方法）
- Affected code: `core/cfg/region_analyzer.py`（_find_try_else_blocks 方法，如需要）
- Affected tests: `tests/exhaustive/with_region/` (10f→0f 目标)
- 必须确保其他 9 个区域测试回归 ≤5f

## 基线状态

### with_region 10 个失败
| 测试 | 源码模式 | 错误类型 | 指令差异 |
|------|----------|----------|----------|
| w035 | `with ctx: for i in range(3): pass` | with+boolop 重复指令 | 42vs44, +2 |
| w043 | `with ctx: for i in range(3): x = i` | with+boolop 重复指令 | 42vs47, +5 |
| w045 | `with ctx: try:...except:...else:...` | with+try else 块错误 | PUSH_NULL vs PUSH_EXC_INFO |
| w058 | `async with ctx as v: x = v` | async with 嵌套 code | 43vs37, -6 |
| w079 | `for i in range(3): with ctx: if i > 1: break` | with+try 嵌套 | 41vs32, -9 |
| w080 | `for i in range(3): with ctx: if i < 1: continue` | with+try 嵌套 | 38vs47, +9 |
| w099 | `with ctx: for x in items: pass` | with+loop 嵌套 | 37vs39, +2 |
| w100 | `with ctx: for x in items: y = x` | with+loop 嵌套 | 39vs41, +2 |
| w102 | `with ctx: try:...except:...finally:...` | with+loop 嵌套 | 54vs59, +5 |
| w30withcustomctx | `class Ctx:...; with Ctx() as c: pass` | with+custom context | 35vs38, +3 |

### 已知问题（当前工作区状态）
- `_generate_with` 中已有部分修改：跳过 TryExceptRegion（handler 全在 with cleanup/exception blocks 中）、`_fix_try_else_in_with` 方法
- 这些修改修复了 w045，但导致 w035/w043/w099/w100 回归（产生 `try:...except:pass except:pass` 无效语法）
- 回归根因：`generate()` 方法的顶层循环仍然处理代表 with 语句自身异常处理的外层 TryExceptRegion

## ADDED Requirements

### Requirement: with_region 10f→0f 修复
系统 SHALL 修复 with_region 的 10 个测试失败，且全量回归 ≤5f。

#### Scenario: Pattern A — with+boolop/loop 重复 prefix 指令（w035/w043/w099/w100）
- **WHEN** with body 中的块属于嵌套 LoopRegion 且该块是 `for_iter_setup` 块时
- **THEN** 跳过重复的 prefix 指令生成，避免 `LOAD_CONST; GET_ITER; FOR_ITER` 等指令被重复生成
- **根因**: `_generate_with` 方法在处理 with body 中的嵌套 LoopRegion 块时，`identify_block_prefix_instructions` 返回了 for_iter_setup 块的前缀指令，但这些指令已经在 LoopRegion 生成时被处理过
- **字节码模式**: with body 块 → LoopRegion.for_iter_setup 块 → prefix 指令重复
- **修复策略**: 在 `_generate_with` 中，当嵌套区域是 LoopRegion 且当前块是其 blocks 成员时，跳过 prefix 指令生成

#### Scenario: Pattern B — with+try/except/else else 块错误（w045）
- **WHEN** `with ctx: try:...except:...else:...` 模式
- **THEN** else 块正确识别为用户代码，而非 with cleanup 代码
- **根因**: `_find_try_else_blocks` 方法将 with cleanup 块（如 block 118）误认为 try 的 else 块，而非实际的 else 代码（如 block 68）
- **修复策略**: 在 `_generate_with` 中跳过 handler 全在 with cleanup/exception blocks 中的 TryExceptRegion（这是 with 自身的异常处理），找到真正的内部 TryExceptRegion，并用 `_fix_try_else_in_with` 重新计算 else_blocks

#### Scenario: Pattern C — with+try 嵌套异常处理冲突（w058/w079/w080）
- **WHEN** with 语句内部包含 try-except 或 if-break/continue 模式
- **THEN** with 的异常处理代码不作为用户 try-except 生成，break/continue 正确识别
- **根因**: WithRegion 的 cleanup_blocks 和 exception_blocks 代表 with 语句自身的 `__exit__` 调用，但 TryExceptRegion 可能覆盖这些块，导致生成无效的 try-except 结构
- **修复策略**: 在 `generate()` 顶层跳过 handler 全在 WithRegion cleanup/exception blocks 中的 TryExceptRegion；在 `_generate_with` 中正确识别 with 内部的真正 try-except

#### Scenario: Pattern D — with+loop 嵌套指令不匹配（w099/w100/w102）
- **WHEN** with 语句内部包含 for 循环或 try-except-finally
- **THEN** 指令数与原始字节码匹配
- **根因**: w099/w100 与 Pattern A 同根因（LoopRegion prefix 重复）；w102 是 finally 块重复生成
- **修复策略**: w099/w100 随 Pattern A 修复；w102 需要单独分析 finally 块重复生成问题

#### Scenario: Pattern E — with+custom context（w30withcustomctx）
- **WHEN** `class Ctx:...; with Ctx() as c: pass` 模式
- **THEN** 指令数匹配（35 vs 35）
- **根因**: class 定义中的指令顺序与原始不同，导致指令数偏多（38 vs 35）
- **修复策略**: 需要分析 class 定义块的生成逻辑

#### Scenario: generate() 顶层 With 异常处理 TryExceptRegion 跳过
- **WHEN** `generate()` 方法遍历 top_level_regions 时遇到 TryExceptRegion
- **THEN** 如果该 TryExceptRegion 的所有 handler_entry_blocks 都在某个 WithRegion 的 cleanup_blocks 或 exception_blocks 中，则跳过该 TryExceptRegion（它代表 with 语句自身的异常处理，不是用户代码）
- **修复策略**: 在 `generate()` 的 top_level_regions 循环中添加跳过逻辑

### Requirement: 回归控制
系统 SHALL 确保每次修改后全量回归 ≤5f。

#### Scenario: 增量验证
- **WHEN** 每次修改核心文件后
- **THEN** 运行 with_region 全量测试确认修复，运行其他 9 个区域测试确认回归 ≤5f

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）

## 关键约束
1. **增量修复**: 每次只修复 1-2 个测试，立即验证无回归
2. **回退策略**: 任何修改导致回归 >5f 时立即回退
3. **优先级**: Pattern A (w035/w043/w099/w100, 最安全) > Pattern B (w045) > Pattern C (w058/w079/w080) > Pattern D (w102) > Pattern E (w30withcustomctx)
4. **核心文件**: 主要修改 `region_ast_generator.py`，必要时修改 `region_analyzer.py`
5. **当前工作区**: 已有部分修改需保留（_fix_try_else_in_with 方法、TryExceptRegion 跳过逻辑），但需解决 generate() 顶层回归问题
