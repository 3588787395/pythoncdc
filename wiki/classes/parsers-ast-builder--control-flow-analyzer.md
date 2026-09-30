---
type: entity
title: ControlFlowAnalyzer
tags:
  - code-kb
related:
  - "[[parsers-ast-builder]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: parsers/ast_builder.py
content_hash: ed1d227dad5ef67f35e0d5e0d0ce9bc6
class: ControlFlowAnalyzer
defined_at: parsers/ast_builder.py:40
class_lines: 750
method_count: 27
bases: []
sources:
  - parsers/ast_builder.py
---

# ControlFlowAnalyzer

定义于 `parsers/ast_builder.py:40`（类体 750 行，27 个方法），所属模块 [[parsers-ast-builder]]。

> 控制流分析器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :43
- `analyze()` :54
- `_build_control_flow_graph()` :107
- `_is_jump_instruction()` :137
- `_get_jump_target()` :161
- `_detect_loop_structures()` :189
- `_detect_exception_blocks_from_table()` :240
- `_detect_exception_blocks()` :276
- `_detect_branch_patterns()` :287
- `_detect_complex_control_flow_patterns()` :316
- `_detect_for_loops()` :333
- `_detect_try_except_blocks()` :369
- `_detect_with_statements()` :442
- `_detect_if_elif_else_chains()` :477
- `_detect_early_return_if_chains()` :532
- `_get_previous_instruction()` :645
- `_get_instruction_at_offset()` :660
- `_get_instructions_before()` :672
- `_get_instructions_after()` :695
- `_get_instructions_in_range()` :718
- `_is_compare_instruction()` :730
- `_detect_unreachable_blocks()` :739
- `get_loop_structures()` :771
- `get_exception_blocks()` :775
- `get_branch_patterns()` :779
- `get_unreachable_blocks()` :783
- `get_control_flow_graph()` :787

## 相关页面

- [[parsers-ast-builder|parsers/ast_builder.py]]
- [[index|Wiki Index]]
