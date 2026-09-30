---
type: entity
title: FastStack
tags:
  - code-kb
related:
  - "[[utils-stack]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: utils/stack.py
content_hash: 4588e2ecf9fc7ea64bda3e974cf245db
class: FastStack
defined_at: utils/stack.py:10
class_lines: 326
method_count: 29
bases: []
sources:
  - utils/stack.py
---

# FastStack

定义于 `utils/stack.py:10`（类体 326 行，29 个方法），所属模块 [[utils-stack]]。

> 快速栈类，模拟Python虚拟机栈

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :13
- `push_history()` :29
- `pop_history()` :35
- `clear_history()` :41
- `has_history()` :45
- `push()` :49
- `pop()` :65
- `top()` :75
- `peek()` :86
- `empty()` :94
- `size()` :98
- `copy()` :102
- `clear()` :122
- `track_variable()` :128
- `_track_variable()` :170
- `_track_variable_lifecycle()` :174
- `push_scope()` :196
- `pop_scope()` :212
- `get_variables()` :245
- `get_variable_operations()` :249
- `get_variable_scopes()` :253
- `get_variable_types()` :257
- `add_variable_scope()` :261
- `get_variable_lifecycles()` :280
- `get_current_scope()` :284
- `peek_depth()` :291
- `is_variable_alive()` :297
- `get_variable_definitions()` :309
- `get_variable_references()` :323

## 相关页面

- [[utils-stack|utils/stack.py]]
- [[index|Wiki Index]]
