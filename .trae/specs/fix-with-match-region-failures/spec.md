# 修复 with_region 和 match_region 测试失败规范

## Why
当前反编译器在 with_region 有 9 个测试失败、match_region 有 4 个测试失败。之前的修复尝试（已作为未提交更改存在于工作区）虽然修复了 5 个 with_region 测试，但导致 match_region 从 4f 暴涨至 44f（40 个回归），不可接受。需要从基线代码出发，采用更精细的增量修复策略。

## What Changes
- **回退当前未提交更改**：当前 `region_ast_generator.py` 的 702 行 diff 引入了 40 个 match_region 回归，必须先回退到基线
- **增量修复 with_region 9f**：逐个分析并修复，每次修改后验证 match_region 无回归
- **增量修复 match_region 4f**：在 with_region 修复基础上，修复 match_region 剩余 4 个失败
- 只修改 `region_ast_generator.py`，不修改 `region_analyzer.py`

## Impact
- Affected code: `core/cfg/region_ast_generator.py`
- Affected tests: `tests/exhaustive/with_region/` (9f→0f), `tests/exhaustive/match_region/` (4f→0f)
- 必须确保其他区域测试无回归

## 基线状态（已提交代码）

### with_region 9 个失败
| 测试 | 源码 | 错误类型 |
|------|------|----------|
| w035 | `with ctx: for i in range(3): pass` | 指令数不匹配 |
| w043 | `with ctx: for i in range(3): x = i` | 指令数不匹配 |
| w058 | `async def f(): async with ctx as v: x = v` | 嵌套code object指令数不匹配(43 vs 37) |
| w079 | `for i in range(3): with ctx: if i > 1: break` | 指令数不匹配(41 vs 32) |
| w080 | `for i in range(3): with ctx: if i < 1: continue` | 指令数不匹配 |
| w099 | `with ctx: for x in items: pass` | 指令数不匹配 |
| w100 | `with ctx: for x in items: y = x` | 指令数不匹配 |
| w102 | `with ctx: result=None; try: result=compute(); except: result=0; finally: cleanup()` | 指令数不匹配(54 vs 59) |
| w30withcustomctx | `class Ctx: ...; with Ctx() as c: pass` | 指令数不匹配(35 vs 38) |

### match_region 4 个失败
| 测试 | 错误类型 |
|------|----------|
| m075 | 指令数不匹配(24 vs 28) |
| m083 | 指令数不匹配(99 vs 107) |
| m106 | 嵌套code object指令11参数不匹配: small vs None |
| m107 | 嵌套code object指令数不匹配(74 vs 76) |

## ADDED Requirements

### Requirement: with_region 修复（9f→0f）
系统 SHALL 修复 with_region 的 9 个测试失败，且不引入 match_region 回归。

#### Scenario: w035/w043/w099/w100 修复（with body 含 LoopRegion 重复 prefix 指令）
- **WHEN** with body 中的块属于嵌套 LoopRegion 且该块是 `for_iter_setup` 块时
- **THEN** 跳过重复的 prefix 指令生成，避免 `LOAD_CONST; GET_ITER; FOR_ITER` 等指令被重复生成
- **根因**: `_generate_with` 方法在处理 with body 中的嵌套 LoopRegion 块时，`identify_block_prefix_instructions` 返回了 for_iter_setup 块的前缀指令（包含 FOR_ITER 等），但这些指令已经在 LoopRegion 生成时被处理过
- **字节码模式**: with body 块 → LoopRegion.for_iter_setup 块 → prefix 指令重复
- **修复策略**: 在 `_generate_with` 中，当嵌套区域是 LoopRegion 且当前块是其 `for_iter_setup` 块时，跳过 prefix 指令生成

#### Scenario: w079/w080 修复（with+if+break/continue）
- **WHEN** `for i in range(3): with ctx: if i > 1: break` 模式
- **THEN** 反编译为 `for i in range(3): with ctx: if i > 1: break`（正确包含 break/continue）
- **根因**: IfRegion 的 then_blocks 只包含 with __exit__ 调用的 NOP 块，break/continue 在 __exit__ 调用之后的块中。当前 `_if_generate_then_branch` 不识别 "with __exit__ + break/continue" 模式
- **字节码模式**: then_block 含 `LOAD_CONST None ×3; PRECALL 2; CALL 2; POP_TOP; POP_TOP; LOAD_CONST None; RETURN_VALUE`（break）或 `...; POP_TOP; JUMP_FORWARD`（continue）
- **修复策略**: 在 `_if_generate_then_branch` 中，当 then_stmts 为空或只有 Pass 时，检测条件块的其他后继块中是否存在 "PRECALL+CALL + RETURN_VALUE/JUMP" 模式（with __exit__ + break/continue），直接生成 Break/Continue AST 节点

#### Scenario: w058 修复（async with 嵌套代码对象）
- **WHEN** `async def f(): async with ctx as v: x = v` 模式
- **THEN** 嵌套代码对象的指令数匹配（43 vs 43）
- **根因**: async with 的嵌套代码对象（协程体）中，`STORE_FAST; LOAD_FAST; STORE_FAST` 被错误地替换为 `POP_TOP`，丢失了 `v = __aenter__; x = v` 的赋值
- **修复策略**: 需要分析嵌套代码对象生成逻辑，确保 async with 的 `as v` 变量赋值和后续使用正确保留

#### Scenario: w102 修复（with+try/except/finally）
- **WHEN** `with ctx: result=None; try: result=compute(); except: result=0; finally: cleanup()` 模式
- **THEN** 指令数匹配（54 vs 54）
- **根因**: with body 中的 try-except-finally 结构生成时，`cleanup()` 调用被重复生成（finally 块在 except handler 之后又被生成一次），导致指令数偏多（59 vs 54）
- **修复策略**: 在 `_generate_with` 处理嵌套 TryExceptRegion 时，避免 finally 块的重复生成

#### Scenario: w30withcustomctx 修复（自定义上下文管理器）
- **WHEN** `class Ctx: ...; with Ctx() as c: pass` 模式
- **THEN** 指令数匹配（35 vs 35）
- **根因**: class 定义中的 `LOAD_BUILD_CLASS` 和 `MAKE_FUNCTION` 指令顺序与原始不同，导致指令数偏多（38 vs 35）。可能是 with body 前的 class 定义块生成顺序问题
- **修复策略**: 需要分析 class 定义块的生成逻辑，确保指令顺序与原始匹配

### Requirement: match_region 修复（4f→0f）
系统 SHALL 修复 match_region 的 4 个测试失败，且不引入 with_region 回归。

#### Scenario: m075 修复（match case body 中 BoolOp/If 嵌套）
- **WHEN** match case body 包含 if 语句或 BoolOp 表达式时
- **THEN** 指令数匹配（24 vs 24）
- **根因**: match case body 中的 if 语句被错误展开，生成了多余的指令（28 vs 24）

#### Scenario: m083 修复（match guard 含函数调用）
- **WHEN** match guard 包含函数调用（如 `case x if guard_fn(x):`）时
- **THEN** 指令数匹配（99 vs 99）
- **根因**: `_collect_guard_pattern_blocks` 的 `allowed` 集合不包含 `PUSH_NULL`、`PRECALL`、`CALL` 等函数调用相关操作码，导致 guard 块被误判为非 pattern 块，guard 表达式丢失

#### Scenario: m106 修复（match guard BoolOp）
- **WHEN** match guard 包含 BoolOp（如 `case x if x > 0 and x < 10:`）时
- **THEN** 嵌套代码对象指令参数匹配
- **根因**: guard 中的 BoolOp 表达式重建不正确，导致 LOAD_CONST 参数不匹配（small vs None）

#### Scenario: m107 修复（match in func return）
- **WHEN** match 语句在函数内作为返回值时
- **THEN** 嵌套代码对象指令数匹配（74 vs 74）
- **根因**: match 语句的 body 块中多生成了 POP_TOP 指令（76 vs 74）

### Requirement: 零回归保证
系统 SHALL 确保每次修改后：
1. with_region 失败数不增加
2. match_region 失败数不增加
3. 其他 8 个区域测试无回归

#### Scenario: 增量验证
- **WHEN** 每次修改 `region_ast_generator.py` 后
- **THEN** 运行 with_region 和 match_region 全量测试确认无回归

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）

## 关键约束
1. **只修改 region_ast_generator.py**：不修改 region_analyzer.py
2. **增量修复**：每次只修复 1-2 个测试，立即验证无回归
3. **回退策略**：任何修改导致回归时立即回退
4. **优先级**: w035/w043/w099/w100（最安全）> m083（简单）> w079/w080（复杂）> w058/w102/w30withcustomctx/m075/m106/m107（最难）
