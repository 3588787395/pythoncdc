# BoolOp/Ternary 区域失败测试修复 Spec

## Why
BoolOp区域9f/123p(93.2%)和Ternary区域8f/81p(91.0%)存在可修复的失败测试。部分失败可在AST生成层(region_ast_generator.py)修复，部分需要region_analyzer.py修改。

## What Changes
- 修复 `_build_boolop_expression` 中混合and/or链的segment构建逻辑 (bo24)
- 修复 `_build_boolop_expression` 中UNARY_NOT在boolop链中的处理 (bo43)
- 修复 `_if_extract_condition_from_instructions` 中TernaryRegion merge_ctx='compare'的检测 (ternary11)
- 修复 `_loop_generate_for` 中TernaryRegion merge_ctx='iter'的迭代器查找逻辑 (ternary13)
- 修复 `_generate_ternary` 中try块内ternary赋值的重复生成和value_target丢失 (ternary15)
- 修复 `_generate_ternary` 中func_call_info上下文的ternary作为函数参数的处理 (te04)

## Impact
- Affected code: `core/cfg/region_analyzer.py` (只读，不修改)
- Affected code: `core/cfg/region_ast_generator.py` (核心修改文件)
- 测试文件: `tests/exhaustive/boolop/` 和 `tests/exhaustive/ternary/`

## 根因分析与可修复性评估

### BoolOp失败测试 (9f)

#### bo24orandor (3f): `a or b and c or False` — 指令数不匹配 16 vs 14
- **错误**: 反编译输出 `a or b\nc or False\n` (两个独立语句)
- **根因**: `_build_boolop_expression` 的segment构建中，`b and c` 的and子链块不在op_chain中。字节码中 `LOAD_NAME(b)` 后跟 `POP_JUMP_FORWARD_IF_FALSE`（and短路跳转），但这个跳转不在op_chain的chain块中。
- **字节码模式**:
  ```
  LOAD_NAME(a)        ← chain块1 (or)
  JUMP_IF_TRUE_OR_POP
  LOAD_NAME(b)        ← chain块2 (and) — 但POP_JUMP_IF_FALSE指向偏移14
  POP_JUMP_FORWARD_IF_FALSE  ← and短路跳转，不在op_chain中！
  LOAD_NAME(c)        ← chain块3 (or)
  JUMP_IF_TRUE_OR_POP
  LOAD_CONST(False)   ← 最终值块
  ```
- **可修复性**: ✅ **可在AST层修复** — 需要在`_build_boolop_expression`中检测非op_chain块中的短路跳转指令，将其加入正确的segment

#### bo31andinif (3f): `if a and b: a = 0` — BOOL_OP未找到
- **错误**: 反编译输出 `if a: if b: a = 0` (嵌套if)
- **根因**: region_analyzer将 `if a and b:` 识别为IfRegion（两个嵌套IfRegion），而非BoolOpRegion。AST层无法创建BoolOpRegion。
- **可修复性**: ❌ **需region_analyzer修改** — 在AST层无法创建不存在的BoolOpRegion

#### bo42boolopinlistcomp (1f): `[x for x in items if x > 0 and x < 100]` — BOOL_OP未找到
- **错误**: 反编译输出 `return [x for x in items if x > 0 if x < 100]` (两个if过滤器)
- **根因**: 列表推导中的BoolOp被comprehension_generator处理为两个独立的if过滤器。语义等价但测试期望BoolOp。
- **可修复性**: ❌ **需region_analyzer修改** — comprehension中的BoolOp识别

#### bo43complexnotandor (1f): `not (a and b) or (c and not d)` — 指令数不匹配 19 vs 11
- **错误**: 反编译输出 `not (a and c and not d)` (丢失b，结构错误)
- **根因**: `_build_boolop_expression` 在处理UNARY_NOT时，将 `(a and b)` 的结果块（含UNARY_NOT）和 `(c and not d)` 的块合并，导致b丢失。UNARY_NOT块被当作普通chain块处理，其前面的LOAD_NAME(b)被跳过。
- **字节码模式**:
  ```
  LOAD_NAME(a)        ← chain块1 (and)
  JUMP_IF_FALSE_OR_POP
  LOAD_NAME(b)        ← chain块2 (and) — 值块
  UNARY_NOT           ← merge块中的not操作
  JUMP_IF_TRUE_OR_POP ← or短路跳转
  LOAD_NAME(c)        ← chain块3 (and)
  JUMP_IF_FALSE_OR_POP
  LOAD_NAME(d)        ← chain块4 (and) — 值块
  UNARY_NOT           ← 值块中的not操作
  ```
- **可修复性**: ✅ **可在AST层修复** — 需要改进UNARY_NOT在boolop链中的处理：UNARY_NOT后的JUMP_IF_TRUE_OR_POP表示or操作

#### bo50andorreturnexpr (1f): `return a if a > 0 else (b if b > 0 else c)` — BOOL_OP未找到
- **错误**: 反编译输出 `return a if a > 0 else b if b > 0 else c` (三元表达式)
- **根因**: 源码是嵌套三元表达式，但测试期望BOOL_OP区域。region_analyzer将其识别为TernaryRegion而非BoolOpRegion。
- **可修复性**: ❌ **需region_analyzer修改** — 区域识别层面的冲突

### Ternary失败测试 (8f)

#### te04ternaryfuncparam (2f): `print("max" if a > b else "min", a if a > 0 else b)` — 嵌套code不匹配
- **错误**: 反编译输出 `'max' if a > b else 'min'\na if a > 0 else b` (两个独立Expr语句)
- **根因**: 两个ternary表达式作为print()的参数，但被生成为独立的Expr语句。TernaryRegion没有func_call_info上下文，或者func_call_info处理不正确。
- **可修复性**: ⚠️ **可能可在AST层修复** — 需要改进func_call_info的处理，将多个连续的ternary表达式合并为一个Call节点

#### ternary11_in_if (1f): `if (a if c else b) > threshold: process()` — 指令数不匹配 15 vs 10
- **错误**: 反编译输出 `a if c else b` (仅ternary表达式，缺少if语句和比较)
- **根因**: TernaryRegion merge_ctx='compare' 被生成为独立的Expr(IfExp)语句，而_if_extract_condition_from_instructions没有检测到这个TernaryRegion并将其与COMPARE_OP组合为if条件。
- **字节码模式**:
  ```
  LOAD_NAME(c)        ← 条件
  POP_JUMP_IF_FALSE   ← ternary分支
  LOAD_NAME(a)        ← true值
  JUMP_FORWARD        ← ternary合并
  LOAD_NAME(b)        ← false值
  LOAD_NAME(threshold) ← 比较操作数
  COMPARE_OP(>)       ← 比较操作
  POP_JUMP_IF_FALSE   ← if分支
  ```
- **可修复性**: ✅ **可在AST层修复** — 需要在`_if_extract_condition_from_instructions`中检测TernaryRegion merge_ctx='compare'，提取ternary表达式并与后续COMPARE_OP组合

#### ternary12_in_while (1f): `while (next_item() if has_more() else None): pass` — TERNARY未找到
- **错误**: 反编译输出 `if has_more() and next_item(): pass\nwhile has_more(): pass`
- **根因**: region_analyzer将while条件中的ternary识别为BoolOpRegion + WhileRegion，而非TernaryRegion。
- **可修复性**: ❌ **需region_analyzer修改** — while条件中的ternary需要region_analyzer识别

#### ternary13_in_for_iter (1f): `for x in (list_a if use_a else list_b): pass` — 语法错误
- **错误**: 反编译输出 `list_a if use_a else list_b\nfor x in True: pass` (ternary在for之前，非迭代器)
- **根因**: TernaryRegion merge_ctx='iter' 被生成为独立的Expr(IfExp)语句，而`_loop_generate_for`的fallback逻辑没有找到这个ternary表达式作为迭代器。
- **字节码模式**:
  ```
  LOAD_NAME(use_a)    ← 条件
  POP_JUMP_IF_FALSE   ← ternary分支
  LOAD_NAME(list_a)   ← true值
  JUMP_FORWARD        ← ternary合并
  LOAD_NAME(list_b)   ← false值
  GET_ITER            ← 获取迭代器
  FOR_ITER            ← for循环迭代
  ```
- **可修复性**: ✅ **可在AST层修复** — 需要修复`_loop_generate_for`中ternary表达式的查找逻辑：当for_iter_setup块不存在时，在已生成的ast_nodes中查找IfExp表达式

#### ternary15_in_try (1f): `try: val = expr if cond else alt\nexcept: val = None` — 指令数不匹配 17 vs 24
- **错误**: 反编译输出 `try:\n    expr if cond else alt\n    expr if cond else alt\nexcept:\n    val = None` (重复ternary，缺少赋值)
- **根因**: TernaryRegion在try块中被生成两次（一次从top_level处理，一次从TryExceptRegion children处理），且value_target(val)丢失。
- **可修复性**: ⚠️ **可能可在AST层修复** — 需要：(1)防止TernaryRegion在try块中被重复生成 (2)在else分支中检测value_target

#### ternary17_in_lambda (1f): `f = lambda x: (process(x) if valid(x) else None)` — TERNARY未找到
- **错误**: 反编译输出 `f = lambda x: None` (lambda体完全错误)
- **根因**: Lambda体是独立的code object，其中的ternary需要递归反编译。当前递归反编译可能不完整。
- **可修复性**: ❌ **需region_analyzer修改** — lambda内部的ternary需要特殊处理

#### ternary20_complex_practical (1f): f-string + ternary — 语法错误
- **错误**: 反编译输出 `<JoinedStr> if bytes_val < 1024 else bytes_val < 1048576` (JoinedStr字面量)
- **根因**: f-string重建失败，产生`<JoinedStr>`字面量字符串。这是code_generator.py的问题。
- **可修复性**: ❌ **需code_generator修改** — f-string生成不在region_ast_generator.py范围

## ADDED Requirements

### Requirement: BoolOp混合and/or链修复 (bo24)
系统 SHALL 在 `_build_boolop_expression` 中正确处理混合and/or链，当op_chain中缺少and短路跳转块时，从region.blocks中补充检测。

#### Scenario: bo24 or-and-or链
- **WHEN** 反编译 `a or b and c or False` 时
- **THEN** 生成单个BoolOp(or, [Name(a), BoolOp(and, [Name(b), Name(c)]), Constant(False)])

### Requirement: BoolOp UNARY_NOT处理修复 (bo43)
系统 SHALL 在 `_build_boolop_expression` 中正确处理UNARY_NOT操作符，将其作为当前segment的一部分而非跳过。

#### Scenario: bo43 complex not-and-or
- **WHEN** 反编译 `not (a and b) or (c and not d)` 时
- **THEN** 生成 BoolOp(or, [UnaryOp(not, BoolOp(and, [Name(a), Name(b)])), BoolOp(and, [Name(c), UnaryOp(not, Name(d))])])

### Requirement: Ternary在if条件中修复 (ternary11)
系统 SHALL 在 `_if_extract_condition_from_instructions` 中检测TernaryRegion merge_ctx='compare'，将ternary表达式与后续COMPARE_OP组合为if条件。

#### Scenario: ternary11 in if condition
- **WHEN** 反编译 `if (a if c else b) > threshold: process()` 时
- **THEN** 生成 If(test=Compare(IfExp(Name(c), Name(a), Name(b)), [Gt], [Name(threshold)]), body=[Expr(Call(Name(process)))])

### Requirement: Ternary在for迭代器中修复 (ternary13)
系统 SHALL 在 `_loop_generate_for` 中正确查找TernaryRegion merge_ctx='iter'的表达式作为迭代器。

#### Scenario: ternary13 in for iter
- **WHEN** 反编译 `for x in (list_a if use_a else list_b): pass` 时
- **THEN** 生成 For(target=Name(x), iter=IfExp(Name(use_a), Name(list_a), Name(list_b)), body=[Pass])

### Requirement: Ternary在try块中修复 (ternary15)
系统 SHALL 防止TernaryRegion在try块中被重复生成，并正确检测value_target。

#### Scenario: ternary15 in try
- **WHEN** 反编译 `try: val = expr if cond else alt\nexcept: val = None` 时
- **THEN** 生成 Try(body=[Assign(Name(val), IfExp(...))], handlers=[ExceptHandler(body=[Assign(Name(val), Constant(None))])])

### Requirement: Ternary作为函数参数修复 (te04)
系统 SHALL 将多个连续的ternary表达式合并为一个Call节点的参数。

#### Scenario: te04 ternary as function args
- **WHEN** 反编译 `print("max" if a > b else "min", a if a > 0 else b)` 时
- **THEN** 生成 Expr(Call(Name(print), args=[IfExp(...), IfExp(...)]))

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）

## 不可修复测试标记

以下测试需region_analyzer.py修改，在AST层无法修复：

| 测试 | 错误类型 | 根因 | 需要的修改 |
|------|---------|------|-----------|
| bo31 (3f) | BOOL_OP未找到 | `if a and b:` 被识别为IfRegion | region_analyzer: BoolOp-If冲突消解 |
| bo42 (1f) | BOOL_OP未找到 | 列表推导中的BoolOp | region_analyzer: comprehension BoolOp识别 |
| bo50 (1f) | BOOL_OP未找到 | 嵌套ternary vs BoolOp冲突 | region_analyzer: 区域类型判定 |
| ternary12 (1f) | TERNARY未找到 | while条件中的ternary | region_analyzer: while条件ternary识别 |
| ternary17 (1f) | TERNARY未找到 | lambda体中的ternary | region_analyzer: lambda递归反编译 |
| ternary20 (1f) | 语法错误 | f-string重建失败 | code_generator: JoinedStr生成 |
