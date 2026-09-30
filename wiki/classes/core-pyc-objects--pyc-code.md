---
type: entity
title: PycCode
tags:
  - code-kb
related:
  - "[[core-pyc-objects]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/pyc_objects.py
content_hash: 03da2e976f92850cf47f18555b7701fc
class: PycCode
defined_at: core/pyc_objects.py:172
class_lines: 516
method_count: 12
bases: [PycObject]
sources:
  - core/pyc_objects.py
---

# PycCode

定义于 `core/pyc_objects.py:172`（类体 516 行，12 个方法），所属模块 [[core-pyc-objects]]。

> Python代码对象

## 继承与 override

- `PycObject`

override（与仓库内基类同名方法）：

- PycObject: __init__, __str__, load

## 方法清单

- `__init__()` :175
- `from_python_code()` :200
- `to_python_code()` :267
- `get_const()` :392
- `get_name()` :400
- `get_local()` :408
- `mark_global()` :421
- `get_cell_var()` :425
- `load()` :452
- `_parse_varint()` :575
- `exception_table_entries()` :602
- `__str__()` :672

## 相关页面

- [[core-pyc-objects|core/pyc_objects.py]]
- [[index|Wiki Index]]
