---
type: entity
title: BasicBlock
tags:
  - code-kb
related:
  - "[[core-cfg-basic-block]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/basic_block.py
content_hash: ea0f7a93156b1c5cfb86526112589e66
class: BasicBlock
defined_at: core/cfg/basic_block.py:38
class_lines: 338
method_count: 30
bases: []
sources:
  - core/cfg/basic_block.py
---

# BasicBlock

定义于 `core/cfg/basic_block.py:38`（类体 338 行，30 个方法），所属模块 [[core-cfg-basic-block]]。

> 控制流图中的基本块

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :50
- `conditional_successors()` :92
- `id()` :96
- `reset_id_counter()` :101
- `add_instruction()` :105
- `add_instructions()` :118
- `get_first_instruction()` :128
- `get_last_instruction()` :132
- `add_predecessor()` :136
- `add_successor()` :145
- `remove_predecessor()` :155
- `remove_successor()` :164
- `is_conditional()` :174
- `is_unconditional_jump()` :198
- `is_return()` :216
- `is_raise()` :232
- `has_jump_instruction()` :248
- `get_jump_targets()` :263
- `dominates()` :284
- `strictly_dominates()` :296
- `post_dominates()` :299
- `strictly_post_dominates()` :302
- `__iter__()` :305
- `__len__()` :309
- `__bool__()` :313
- `__hash__()` :317
- `__eq__()` :320
- `__repr__()` :325
- `__str__()` :328
- `to_dict()` :356

## 相关页面

- [[core-cfg-basic-block|core/cfg/basic_block.py]]
- [[index|Wiki Index]]
