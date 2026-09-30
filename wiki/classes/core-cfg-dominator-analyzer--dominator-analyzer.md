---
type: entity
title: DominatorAnalyzer
tags:
  - code-kb
related:
  - "[[core-cfg-dominator-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/dominator_analyzer.py
content_hash: c13ca7257ca7ad7034597c8d4fe8b401
class: DominatorAnalyzer
defined_at: core/cfg/dominator_analyzer.py:40
class_lines: 274
method_count: 16
bases: []
sources:
  - core/cfg/dominator_analyzer.py
---

# DominatorAnalyzer

定义于 `core/cfg/dominator_analyzer.py:40`（类体 274 行，16 个方法），所属模块 [[core-cfg-dominator-analyzer]]。

> 支配节点分析器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :48
- `analyze()` :52
- `dominates()` :59
- `_compute_dominators()` :64
- `_compute_immediate_dominators()` :102
- `_compute_dominated_blocks()` :128
- `_compute_post_dominators()` :137
- `_compute_immediate_post_dominators()` :223
- `get_post_dominance_frontier()` :244
- `find_nearest_common_post_dominator()` :255
- `find_nearest_common_post_dominator_two()` :281
- `is_dominator()` :284
- `strictly_dominates()` :287
- `strictly_post_dominates()` :290
- `get_dominance_frontier()` :293
- `compute_all_dominance_frontiers()` :307

## 相关页面

- [[core-cfg-dominator-analyzer|core/cfg/dominator_analyzer.py]]
- [[index|Wiki Index]]
