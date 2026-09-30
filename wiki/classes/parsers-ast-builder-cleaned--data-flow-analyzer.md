---
type: entity
title: DataFlowAnalyzer
tags:
  - code-kb
related:
  - "[[parsers-ast-builder-cleaned]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: parsers/ast_builder_cleaned.py
content_hash: 26256f36b353d6a4ebcd9557fad4df1a
class: DataFlowAnalyzer
defined_at: parsers/ast_builder_cleaned.py:792
class_lines: 266
method_count: 16
bases: []
sources:
  - parsers/ast_builder_cleaned.py
---

# DataFlowAnalyzer

定义于 `parsers/ast_builder_cleaned.py:792`（类体 266 行，16 个方法），所属模块 [[parsers-ast-builder-cleaned]]。

> 数据流分析器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :795
- `analyze()` :803
- `_build_def_use_chains()` :811
- `_get_variable_name()` :837
- `_analyze_live_variables()` :866
- `_analyze_reaching_definitions()` :912
- `_analyze_available_expressions()` :947
- `_analyze_very_busy_expressions()` :972
- `_get_predecessors()` :998
- `_get_successors()` :1006
- `_apply_kill_function()` :1018
- `_apply_gen_function()` :1033
- `get_live_variables()` :1043
- `get_reaching_definitions()` :1047
- `get_available_expressions()` :1051
- `get_very_busy_expressions()` :1055

## 相关页面

- [[parsers-ast-builder-cleaned|parsers/ast_builder_cleaned.py]]
- [[index|Wiki Index]]
