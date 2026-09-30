---
type: entity
title: RegionAnalyzer
tags:
  - code-kb
related:
  - "[[core-cfg-structured-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/structured_analyzer.py
content_hash: ff7ce3e41e1d6ac510b30620368bd8a1
class: RegionAnalyzer
defined_at: core/cfg/structured_analyzer.py:15845
class_lines: 228
method_count: 12
bases: []
sources:
  - core/cfg/structured_analyzer.py
---

# RegionAnalyzer

定义于 `core/cfg/structured_analyzer.py:15845`（类体 228 行，12 个方法），所属模块 [[core-cfg-structured-analyzer]]。

> 区域分析器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :15852
- `analyze()` :15864
- `_find_single_entry_regions()` :15877
- `_expand_region()` :15888
- `_find_loop_regions()` :15914
- `_find_conditional_regions()` :15929
- `_analyze_conditional_region()` :15943
- `_find_conditional_merge()` :15966
- `_reachable_blocks()` :15989
- `_collect_path()` :16016
- `get_region_for_block()` :16044
- `get_region_entry()` :16059

## 相关页面

- [[core-cfg-structured-analyzer|core/cfg/structured_analyzer.py]]
- [[index|Wiki Index]]
