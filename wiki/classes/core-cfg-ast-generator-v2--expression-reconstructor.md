---
type: entity
title: ExpressionReconstructor
tags:
  - code-kb
related:
  - "[[core-cfg-ast-generator-v2]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/ast_generator_v2.py
content_hash: d79f62e6d3deab295fec52d22bb10ebe
class: ExpressionReconstructor
defined_at: core/cfg/ast_generator_v2.py:20
class_lines: 2660
method_count: 20
bases: []
sources:
  - core/cfg/ast_generator_v2.py
---

# ExpressionReconstructor

定义于 `core/cfg/ast_generator_v2.py:20`（类体 2660 行，20 个方法），所属模块 [[core-cfg-ast-generator-v2]]。

> 表达式重建器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :27
- `reset()` :44
- `_open_ternary_region()` :54
- `_track_ternary_region()` :62
- `_close_ternary_region()` :102
- `_flatten_dict_merge_to_kwargs()` :124
- `_flatten_dict_merge_to_dict_items()` :159
- `reconstruct()` :195
- `_process_instruction()` :223
- `_get_binary_op()` :2185
- `_get_binary_op_from_arg()` :2207
- `_get_unary_op()` :2237
- `_dict_equal()` :2247
- `_is_yield_from_pattern()` :2273
- `_reconstruct_yield_from()` :2297
- `_get_compare_op()` :2344
- `_load_instr_to_ast()` :2361
- `_parse_comprehension_from_code()` :2386
- `_extract_comp_elt()` :2482
- `_build_expr_from_instrs()` :2571

## 相关页面

- [[core-cfg-ast-generator-v2|core/cfg/ast_generator_v2.py]]
- [[index|Wiki Index]]
