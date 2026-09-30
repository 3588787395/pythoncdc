---
type: entity
title: LoopAnalyzer
tags:
  - code-kb
related:
  - "[[core-cfg-dominator-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/dominator_analyzer.py
content_hash: c13ca7257ca7ad7034597c8d4fe8b401
class: LoopAnalyzer
defined_at: core/cfg/dominator_analyzer.py:315
class_lines: 189
method_count: 11
bases: []
sources:
  - core/cfg/dominator_analyzer.py
---

# LoopAnalyzer

定义于 `core/cfg/dominator_analyzer.py:315`（类体 189 行，11 个方法），所属模块 [[core-cfg-dominator-analyzer]]。

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :316
- `analyze()` :323
- `_find_back_edges()` :329
- `_classify_loop_headers()` :343
- `_compute_loop_bodies()` :364
- `_compute_natural_loop()` :388
- `_compute_for_loop_body()` :416
- `_get_for_iter_fall_through()` :461
- `_compute_loop_depths()` :476
- `_can_reach()` :487
- `get_all_loops()` :502

## 相关页面

- [[core-cfg-dominator-analyzer|core/cfg/dominator_analyzer.py]]
- [[index|Wiki Index]]
