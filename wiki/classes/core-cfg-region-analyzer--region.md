---
type: entity
title: Region
tags:
  - code-kb
related:
  - "[[core-cfg-region-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/region_analyzer.py
content_hash: f813391da783fa0a1a7a6e5ec1a1b229
class: Region
defined_at: core/cfg/region_analyzer.py:204
class_lines: 157
method_count: 26
bases: []
sources:
  - core/cfg/region_analyzer.py
---

# Region

定义于 `core/cfg/region_analyzer.py:204`（类体 157 行，26 个方法），所属模块 [[core-cfg-region-analyzer]]。

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__hash__()` :214
- `mark_trailing_return_none()` :217
- `add_child()` :221
- `get_content_blocks()` :235
- `find_enclosing_parent()` :238
- `find_descendant_region_for_block()` :250
- `iter_descendants()` :266
- `annotate_structural_roles()` :272
- `annotate_cond_recheck()` :276
- `get_score_merge_block()` :280
- `precompute_analysis()` :284
- `is_block_entry()` :288
- `contains_block()` :292
- `is_block_in_body()` :296
- `else_block_conflict()` :300
- `get_with_body_orphan_instructions()` :304
- `get_compactness_successors()` :309
- `get_offset_range()` :314
- `get_if_branch_boundary_stop()` :322
- `interrupts_boolop_forward_chain()` :327
- `can_be_ternary_header()` :332
- `get_if_body_blocks()` :337
- `get_else_blocks_for_merge()` :342
- `try_except_absorb_split_from()` :347
- `should_merge_with()` :352
- `preserves_against_nested_match()` :357

## 相关页面

- [[core-cfg-region-analyzer|core/cfg/region_analyzer.py]]
- [[index|Wiki Index]]
