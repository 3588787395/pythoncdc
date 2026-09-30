---
type: entity
title: CompilerOptimizationHandler
tags:
  - code-kb
related:
  - "[[utils-compiler-optimization-handler]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: utils/compiler_optimization_handler.py
content_hash: 1f3b46d01f59bb3d812c756797c3c1b1
class: CompilerOptimizationHandler
defined_at: utils/compiler_optimization_handler.py:36
class_lines: 223
method_count: 10
bases: []
sources:
  - utils/compiler_optimization_handler.py
---

# CompilerOptimizationHandler

定义于 `utils/compiler_optimization_handler.py:36`（类体 223 行，10 个方法），所属模块 [[utils-compiler-optimization-handler]]。

> 编译器优化处理器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :43
- `_init_patterns()` :46
- `analyze_diff()` :60
- `_check_const_pool_diff()` :101
- `_is_dead_code_elimination_const_diff()` :153
- `_is_boolean_folding_result()` :179
- `_is_arithmetic_folding_result()` :204
- `_is_const_folding_pattern()` :212
- `_is_dead_code_elimination()` :223
- `is_compiler_optimization_diff()` :245

## 相关页面

- [[utils-compiler-optimization-handler|utils/compiler_optimization_handler.py]]
- [[index|Wiki Index]]
