---
type: entity
title: TryExceptRegion
tags:
  - code-kb
related:
  - "[[core-cfg-region-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/region_analyzer.py
content_hash: f813391da783fa0a1a7a6e5ec1a1b229
class: TryExceptRegion
defined_at: core/cfg/region_analyzer.py:784
class_lines: 140
method_count: 10
bases: [Region]
sources:
  - core/cfg/region_analyzer.py
---

# TryExceptRegion

定义于 `core/cfg/region_analyzer.py:784`（类体 140 行，10 个方法），所属模块 [[core-cfg-region-analyzer]]。

## 继承与 override

- `Region`

override（与仓库内基类同名方法）：

- Region: annotate_structural_roles, contains_block, else_block_conflict, get_content_blocks, get_else_blocks_for_merge, get_if_branch_boundary_stop, get_offset_range, is_block_entry, precompute_analysis, try_except_absorb_split_from

## 方法清单

- `get_content_blocks()` :798
- `annotate_structural_roles()` :809
- `precompute_analysis()` :812
- `is_block_entry()` :815
- `contains_block()` :818
- `else_block_conflict()` :846
- `get_offset_range()` :849
- `get_if_branch_boundary_stop()` :864
- `get_else_blocks_for_merge()` :889
- `try_except_absorb_split_from()` :893

## 相关页面

- [[core-cfg-region-analyzer|core/cfg/region_analyzer.py]]
- [[index|Wiki Index]]
