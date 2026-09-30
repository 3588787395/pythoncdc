---
type: entity
title: DebugStack
tags:
  - code-kb
related:
  - "[[core-fast-stack]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/fast_stack.py
content_hash: e4d5b599bf5aa9df31222928d1e2b976
class: DebugStack
defined_at: core/fast_stack.py:512
class_lines: 66
method_count: 9
bases: [FastStack]
sources:
  - core/fast_stack.py
---

# DebugStack

定义于 `core/fast_stack.py:512`（类体 66 行，9 个方法），所属模块 [[core-fast-stack]]。

> 调试版本堆栈

## 继承与 override

- `FastStack`

override（与仓库内基类同名方法）：

- FastStack: __init__, pop, push, top

## 方法清单

- `__init__()` :518
- `push()` :529
- `pop()` :534
- `top()` :540
- `_record_operation()` :546
- `get_operation_history()` :551
- `get_operation_count()` :560
- `reset_operations()` :569
- `__repr__()` :574

## 相关页面

- [[core-fast-stack|core/fast_stack.py]]
- [[index|Wiki Index]]
