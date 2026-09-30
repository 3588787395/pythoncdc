---
type: entity
title: StructuredAnalyzer
tags:
  - code-kb
related:
  - "[[core-cfg-structured-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/structured_analyzer.py
content_hash: ff7ce3e41e1d6ac510b30620368bd8a1
class: StructuredAnalyzer
defined_at: core/cfg/structured_analyzer.py:128
class_lines: 15716
method_count: 89
bases: []
sources:
  - core/cfg/structured_analyzer.py
---

# StructuredAnalyzer

定义于 `core/cfg/structured_analyzer.py:128`（类体 15716 行，89 个方法），所属模块 [[core-cfg-structured-analyzer]]。

> 结构化分析器

## 继承与 override

- 无基类（模块内独立定义）

## 机制速览

- **职责**：结构化分析的聚合模块（`StructuredAnalyzer`，89 方法 / 约 1.6 万行），在区域归约之上做结构化整理。补丁标记 1,360 个（占全库 15%）——是补丁最密集的文件之一，见 [[patch-marker-hotspots]]。
- **风险**：补丁密度高 + 体量大，是"补丁式修复"的重灾区；任何改动都应先对照 [[region-reduction-internals]] 的不变量，确认不是在打补丁破坏归约。

## 方法清单

- `__init__()` :135
- `analyze()` :154
- `_identify_loops()` :195
- `_identify_optimized_while_loops()` :420
- `_collect_while_body()` :699
- `_create_while_loop_structure()` :851
- `_analyze_loop()` :908
- `_analyze_loop_else()` :1491
- `_is_valid_else_block()` :1620
- `_collect_else_blocks()` :1726
- `_calculate_jump_target()` :1810
- `_is_while_loop()` :1829
- `_is_if_condition_in_loop()` :2069
- `_is_for_loop()` :2322
- `_identify_conditionals()` :2356
- `_identify_assert_structures()` :2906
- `_is_assert_pattern()` :2994
- `_identify_nop_sequences()` :3172
- `_resolve_structure_overlaps()` :3688
- `_coalesce_chained_comparisons()` :4127
- `_is_conditional_block()` :4456
- `_is_exception_handler_block()` :4506
- `_is_simple_merge_block()` :4520
- `_is_not_condition_pattern()` :4663
- `_analyze_if_structure()` :4721
- `_detect_compound_condition()` :7203
- `_has_chain_compare_pattern()` :8461
- `_detect_elif_chain_in_loop()` :8487
- `_detect_elif_chain()` :8567
- `_reconstruct_compound_conditions_v2()` :9578
- `_has_chain_compare_pattern()` :9684
- `_get_jump_instr()` :9733
- `_find_all_jump_targets()` :9747
- `_branch_exits_scope()` :9776
- `_get_jump_target_block()` :9802
- `_get_fall_through_block()` :9811
- `_is_simple_return_none()` :9820
- `_is_simple_jump_or_return_block()` :9866
- `_get_block_id_by_offset()` :9902
- `_resolve_condition_chain_v2()` :9909
- `_reconstruct_compound_conditions()` :9984
- `_resolve_condition_chain()` :10131
- `_exclude_after_merge()` :10266
- `_find_reachable_blocks()` :10286
- `_find_branch_body_for_elif()` :10311
- `_find_branch_body()` :10426
- `_find_merge_block()` :11655
- `_identify_try_except()` :11706
- `_identify_try_except_from_table()` :11723
- `_identify_simple_try_except()` :11780
- `_collect_else_body()` :12705
- `_find_block_containing_offset()` :12740
- `_collect_try_body()` :12760
- `_collect_nested_try_blocks()` :12891
- `_collect_handler_body()` :12927
- `_extract_exception_type_from_handler()` :13069
- `_extract_exception_name_from_handler()` :13109
- `_extract_exception_name_from_handler_body()` :13160
- `_identify_try_except_legacy()` :13232
- `_identify_try_except_pre_311()` :13279
- `_find_try_entry_for_handler()` :13308
- `_find_try_entry()` :13357
- `_analyze_try_except_structure_v2()` :13382
- `_extract_exception_handler()` :13741
- `_identify_with_structures()` :13825
- `_find_next_with_entry()` :13978
- `_analyze_with_structure()` :14000
- `_analyze_multi_with_structure()` :14034
- `_extract_with_resource()` :14093
- `_reconstruct_expr_from_instrs()` :14165
- `_extract_with_target()` :14273
- `_coalesce_multi_context_withs()` :14360
- `_is_with_chain()` :14438
- `_create_merged_with_structure()` :14738
- `_find_with_body()` :14768
- `_identify_sequences()` :15053
- `_build_hierarchy()` :15238
- `get_structure_for_block()` :15567
- `is_block_in_loop()` :15579
- `get_enclosing_loop()` :15592
- `get_loop_depth()` :15609
- `_identify_match_structures()` :15627
- `_find_match_subject()` :15657
- `_analyze_match_structure()` :15691
- `_extract_match_pattern()` :15754
- `_extract_match_guard()` :15769
- `_extract_match_case_body()` :15777
- `_find_next_case_block()` :15813
- `_find_match_merge_block()` :15827

## 相关页面

- [[core-cfg-structured-analyzer|core/cfg/structured_analyzer.py]]
- [[index|Wiki Index]]
