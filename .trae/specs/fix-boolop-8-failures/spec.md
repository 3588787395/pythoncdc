# BoolOp 8个失败测试修复 Spec

## Why
BoolOp区域当前有8个失败测试(124/132通过, 93.9%)，涉及混合and/or链检测(bo24)、if条件中的and链(bo31)、列表推导式中的boolop(bo42)、以及UNARY_NOT在boolop链中的处理(bo43)。需要修复这些失败以提高反编译器的完备性。

## What Changes
- 修改 `_detect_boolop_short_circuit_chain` 支持混合短路跳转和条件跳转的and/or链 (bo24)
- 修改 `_detect_boolop_conditional_chain` 放宽同目标检查，允许trivial block的不同跳转目标 (bo31)
- 修改 `_detect_boolop_chain_start` 和 `_identify_boolop_regions` 支持BACKWARD_CONDITIONAL_JUMP_OPS (bo42准备)
- 修改 `comprehension_generator._extract_comp_ifs` 合并连续and条件为BoolOp (bo42)
- 修改 `_build_boolop_expression` 正确处理UNARY_NOT块和混合and/or链的分段 (bo43)

## Impact
- Affected code: `core/cfg/region_analyzer.py` (bo24/bo31/bo42区域识别)
- Affected code: `core/cfg/region_ast_generator.py` (bo43 AST生成)
- Affected code: `core/cfg/comprehension_generator.py` (bo42推导式生成)
- 测试文件: `tests/exhaustive/boolop/`

## 根因分析

### bo24 (3f): `a or b and c or False` — 混合短路+条件跳转链断裂
- **错误**: 反编译为 `a or b\nc or False` (两个独立语句)
- **字节码**: Block1(or, JUMP_IF_TRUE_OR_POP) → Block2(and, POP_JUMP_FORWARD_IF_FALSE) → Block3(or, JUMP_IF_TRUE_OR_POP)
- **根因**: `_detect_boolop_short_circuit_chain` 只跟踪SHORT_CIRCUIT_JUMP_OPS块，遇到Block2的POP_JUMP_FORWARD_IF_FALSE时中断链
- **修复**: 在short_circuit_chain中，当遇到FORWARD_CONDITIONAL_JUMP_OPS块时，如果它是当前链块的fall-through后继，继续链检测

### bo31 (3f): `if a and b: a = 0` — and链被识别为嵌套if
- **错误**: 反编译为 `if a: if b: a = 0` (嵌套if)
- **字节码**: Block0(LOAD_NAME(a), POP_JUMP_FORWARD_IF_FALSE→18) → Block6(LOAD_NAME(b), POP_JUMP_FORWARD_IF_FALSE→22)
- **根因**: `_detect_boolop_conditional_chain` 中同目标检查过严，Block0跳转到18(else)，Block6跳转到22(then后的trivial block)，目标不同导致链中断
- **修复**: 当两个跳转目标都是trivial block(仅含LOAD_CONST+RETURN_VALUE)时，不中断链

### bo42 (1f): `[x for x in items if x > 0 and x < 100]` — and条件被拆分为两个if
- **错误**: 反编译为 `[x for x in items if x > 0 if x < 100]`
- **字节码**(listcomp内部): COMPARE_OP(>) → POP_JUMP_BACKWARD_IF_FALSE → COMPARE_OP(<) → POP_JUMP_BACKWARD_IF_FALSE → LIST_APPEND
- **根因**: `_extract_comp_ifs` 将每个POP_JUMP_BACKWARD_IF_FALSE作为独立的if过滤器
- **修复**: 在`_extract_comp_ifs`中，当连续的条件跳转都是POP_JUMP_BACKWARD_IF_FALSE（and模式）且跳转到同一目标时，合并为BoolOp(and)

### bo43 (1f): `not (a and b) or (c and not d)` — UNARY_NOT块处理错误
- **错误**: 反编译为 `not (a and c and not d)` (丢失b，结构错误)
- **字节码**: Block0(and, JUMP_IF_FALSE_OR_POP) → Block6(LOAD_NAME(b)) → Block8(UNARY_NOT, JUMP_IF_TRUE_OR_POP) → Block12(and, JUMP_IF_FALSE_OR_POP) → Block16(LOAD_NAME(d), UNARY_NOT)
- **根因**: op_chain是[(0,'and'),(8,'or'),(12,'and')]，Block8(UNARY_NOT)被当作chain块，但Block6(LOAD_NAME(b))不在chain中。`_build_boolop_expression`将Block8的表达式作为'or'段的值，但丢失了Block6的b
- **修复**: 在`_build_boolop_expression`中，当chain块的fall-through前驱不在chain中时，将该前驱的表达式合并到当前chain块的表达式中

## ADDED Requirements

### Requirement: 混合短路+条件跳转链检测 (bo24)
系统 SHALL 在 `_detect_boolop_short_circuit_chain` 中支持混合SHORT_CIRCUIT_JUMP_OPS和FORWARD_CONDITIONAL_JUMP_OPS的链检测。

#### Scenario: bo24 or-and-or链
- **WHEN** 反编译 `a or b and c or False` 时
- **THEN** 生成单个BoolOp(or, [Name(a), BoolOp(and, [Name(b), Name(c)]), Constant(False)])

### Requirement: if条件中的and链检测 (bo31)
系统 SHALL 在 `_detect_boolop_conditional_chain` 中放宽同目标检查，当跳转目标都是trivial block时不中断链。

#### Scenario: bo31 and-in-if
- **WHEN** 反编译 `if a and b: a = 0` 时
- **THEN** 生成 If(test=BoolOp(and, [Name(a), Name(b)]), body=[Assign(Name(a), Constant(0))])

### Requirement: 列表推导式中and条件合并 (bo42)
系统 SHALL 在 `_extract_comp_ifs` 中将连续的POP_JUMP_BACKWARD_IF_FALSE条件合并为BoolOp(and)。

#### Scenario: bo42 boolop in listcomp
- **WHEN** 反编译 `[x for x in items if x > 0 and x < 100]` 时
- **THEN** 生成 ListComp(elt=Name(x), generators=[comprehension(if=BoolOp(and, [Compare(...), Compare(...)]))])

### Requirement: UNARY_NOT在boolop链中的处理 (bo43)
系统 SHALL 在 `_build_boolop_expression` 中正确处理UNARY_NOT块，将非chain前驱的表达式合并到当前chain块的表达式中。

#### Scenario: bo43 complex not-and-or
- **WHEN** 反编译 `not (a and b) or (c and not d)` 时
- **THEN** 生成 BoolOp(or, [UnaryOp(not, BoolOp(and, [Name(a), Name(b)])), BoolOp(and, [Name(c), UnaryOp(not, Name(d))])])

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）
