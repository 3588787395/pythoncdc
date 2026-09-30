---
type: entity
title: CFGBuilder
tags:
  - code-kb
related:
  - "[[core-cfg-cfg-builder]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/cfg_builder.py
content_hash: 9e17ce9c710392cd37056a41100ca241
class: CFGBuilder
defined_at: core/cfg/cfg_builder.py:68
class_lines: 515
method_count: 15
bases: []
sources:
  - core/cfg/cfg_builder.py
---

# CFGBuilder

定义于 `core/cfg/cfg_builder.py:68`（类体 515 行，15 个方法），所属模块 [[core-cfg-cfg-builder]]。

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :107
- `build()` :113
- `_parse_instructions()` :133
- `_identify_jump_targets()` :165
- `_build_basic_blocks()` :200
- `_connect_blocks()` :237
- `_connect_exception_edges()` :276
- `_identify_exit_blocks()` :300
- `_split_blocks_at_exception_boundaries()` :314
- `_split_block_at_offset()` :327
- `_r4g_stack_delta()` :420
- `_r4g_split_merge_target()` :478
- `_split_blocks_at_short_circuit_merges()` :543
- `_parse_exception_table()` :564
- `get_cfg()` :581

## 相关页面

- [[core-cfg-cfg-builder|core/cfg/cfg_builder.py]]
- [[index|Wiki Index]]
