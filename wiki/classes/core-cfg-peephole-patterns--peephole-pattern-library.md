---
type: entity
title: PeepholePatternLibrary
tags:
  - code-kb
related:
  - "[[core-cfg-peephole-patterns]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/peephole_patterns.py
content_hash: 4f22bd9e7be2a7fa5e5d6ddc1499a0fa
class: PeepholePatternLibrary
defined_at: core/cfg/peephole_patterns.py:82
class_lines: 576
method_count: 9
bases: []
sources:
  - core/cfg/peephole_patterns.py
---

# PeepholePatternLibrary

定义于 `core/cfg/peephole_patterns.py:82`（类体 576 行，9 个方法），所属模块 [[core-cfg-peephole-patterns]]。

> CPython peephole 优化模式库主体。

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :248
- `match_peephole_pattern()` :405
- `is_p1_cond_block()` :450
- `get_p1_match()` :454
- `is_p3_while_true_header()` :460
- `is_p4_chained_compare_header()` :469
- `_match_p1_double_return_ternary()` :477
- `_match_p3_while_true_header()` :590
- `_match_p4_chained_compare_header()` :630

## 相关页面

- [[core-cfg-peephole-patterns|core/cfg/peephole_patterns.py]]
- [[index|Wiki Index]]
