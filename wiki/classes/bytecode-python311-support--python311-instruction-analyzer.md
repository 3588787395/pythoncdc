---
type: entity
title: Python311InstructionAnalyzer
tags:
  - code-kb
related:
  - "[[bytecode-python311-support]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: bytecode/python311_support.py
content_hash: b2c6efa24762564ee4b229ea46e4f1dd
class: Python311InstructionAnalyzer
defined_at: bytecode/python311_support.py:178
class_lines: 304
method_count: 19
bases: []
sources:
  - bytecode/python311_support.py
---

# Python311InstructionAnalyzer

定义于 `bytecode/python311_support.py:178`（类体 304 行，19 个方法），所属模块 [[bytecode-python311-support]]。

> Python 3.11 指令分析器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :181
- `_build_instruction_handlers()` :185
- `analyze_bytecode()` :239
- `_get_opcode_description()` :283
- `_handle_resume()` :303
- `_handle_push_null()` :312
- `_handle_precall()` :321
- `_handle_kw_names()` :331
- `_handle_binary_op()` :350
- `_handle_send()` :374
- `_handle_load_const()` :384
- `_handle_load_name()` :401
- `_handle_call_function()` :418
- `_handle_call_method()` :427
- `_handle_call_method_kw()` :436
- `_handle_binary_add()` :447
- `_handle_binary_subtract()` :456
- `_handle_binary_multiply()` :465
- `_handle_binary_power()` :474

## 相关页面

- [[bytecode-python311-support|bytecode/python311_support.py]]
- [[index|Wiki Index]]
