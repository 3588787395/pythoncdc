---
type: entity
title: ComprehensionGenerator
tags:
  - code-kb
related:
  - "[[core-cfg-comprehension-generator]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/comprehension_generator.py
content_hash: f91a43ad6dae588b339743350ccdb350
class: ComprehensionGenerator
defined_at: core/cfg/comprehension_generator.py:42
class_lines: 2074
method_count: 22
bases: []
sources:
  - core/cfg/comprehension_generator.py
---

# ComprehensionGenerator

定义于 `core/cfg/comprehension_generator.py:42`（类体 2074 行，22 个方法），所属模块 [[core-cfg-comprehension-generator]]。

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :43
- `convert_comprehension_objects()` :46
- `extract_comp_iter_expr()` :83
- `try_generate_comprehension_assign()` :96
- `_generate_pre_comp_stmts()` :640
- `_generate_remaining_stmts()` :740
- `parse_comprehension_inner()` :887
- `_parse_comprehension_inner_impl()` :903
- `_parse_multi_for_comprehension()` :1030
- `_split_dict_comp_kv()` :1183
- `_find_dict_kv_split_point()` :1239
- `_get_stack_delta()` :1318
- `_find_comp_target_names()` :1348
- `_build_comprehension_target()` :1358
- `_find_comp_append_op()` :1379
- `_extract_comp_ifs()` :1392
- `_extract_dict_comp_key_before_ternary()` :1595
- `_extract_dict_comp_value_after_ternary()` :1646
- `_detect_comp_ternary()` :1700
- `_detect_comp_ternary_as_filter()` :1945
- `_build_comp_result()` :2071
- `generate_comprehension_function()` :2088

## 相关页面

- [[core-cfg-comprehension-generator|core/cfg/comprehension_generator.py]]
- [[index|Wiki Index]]
