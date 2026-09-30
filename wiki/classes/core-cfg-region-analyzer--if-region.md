---
type: entity
title: IfRegion
tags:
  - code-kb
related:
  - "[[core-cfg-region-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/region_analyzer.py
content_hash: f813391da783fa0a1a7a6e5ec1a1b229
class: IfRegion
defined_at: core/cfg/region_analyzer.py:363
class_lines: 141
method_count: 13
bases: [Region]
sources:
  - core/cfg/region_analyzer.py
---

# IfRegion

定义于 `core/cfg/region_analyzer.py:363`（类体 141 行，13 个方法），所属模块 [[core-cfg-region-analyzer]]。

## 继承与 override

- `Region`

override（与仓库内基类同名方法）：

- Region: annotate_cond_recheck, annotate_structural_roles, can_be_ternary_header, contains_block, else_block_conflict, get_compactness_successors, get_content_blocks, get_if_body_blocks, get_offset_range, get_score_merge_block, interrupts_boolop_forward_chain, is_block_entry

## 方法清单

- `get_content_blocks()` :377
- `annotate_structural_roles()` :391
- `annotate_cond_recheck()` :394
- `get_score_merge_block()` :398
- `precompute_analysis()` :401
- `is_block_entry()` :404
- `contains_block()` :407
- `else_block_conflict()` :435
- `get_compactness_successors()` :438
- `get_offset_range()` :446
- `interrupts_boolop_forward_chain()` :481
- `can_be_ternary_header()` :485
- `get_if_body_blocks()` :501

## 相关页面

- [[core-cfg-region-analyzer|core/cfg/region_analyzer.py]]
- [[index|Wiki Index]]
