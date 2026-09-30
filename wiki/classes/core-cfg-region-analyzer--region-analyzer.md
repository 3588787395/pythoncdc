---
type: entity
title: RegionAnalyzer
tags:
  - code-kb
related:
  - "[[core-cfg-region-analyzer]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/region_analyzer.py
content_hash: f813391da783fa0a1a7a6e5ec1a1b229
class: RegionAnalyzer
defined_at: core/cfg/region_analyzer.py:1197
class_lines: 27175
method_count: 212
bases: []
sources:
  - core/cfg/region_analyzer.py
---

# RegionAnalyzer

定义于 `core/cfg/region_analyzer.py:1197`（类体 27175 行，212 个方法），所属模块 [[core-cfg-region-analyzer]]。

> 区域分析器 - 基于编译器理论的结构化分析

## 继承与 override

- 无基类（模块内独立定义）

## 机制速览

- **职责**：区域归约识别侧（S1–S4）。入口 `analyze()`（`core/cfg/region_analyzer.py:1335`）跑"固定优先级三阶段流水线"：Phase 1 低层结构（TRY→LOOP→WITH→MATCH→ASSERT）→ Phase 2.5 peephole 预处理 → Phase 2 高层表达式（CHAINED_COMPARE→BOOL_OP→TERNARY）→ IF 条件区域 → 序列区域 → 层级装配。
- **四条不变量**（源码注释 1342-1348）：自底向上归约不回溯；每块唯一归属；嵌套即抽象节点；父区域引用子区域**入口块**。禁止跨层启发式特判。
- **关键数据结构**：`BlockRole`（42 个角色，`region_analyzer.py:127`）、`RegionType`（19 种）、`BlockSemantics`（dataclass，`:191`）、`Region`（`:204`，`add_child` 有环检测 + 父链环检测）。
- **多态消解**：类型差异走 `Region` 基类 19 个覆写点（`:272-310`），避免识别器里散落 isinstance。
- **已知失效模式**：孤儿块释放（`:1410-1425`，te046 修复后需检查"顶级祖先"）、yield-from/await 三元吞并（`:1501-1514`）、match 误识别 vs 三元（`:1458-1475`）。
- **深度阅读**：[[region-reduction-internals]]。

## 方法清单

- `__init__()` :1211
- `_filter_regions()` :1238
- `_stack_effect()` :1244
- `_check_block_has_trailing_return_none()` :1305
- `analyze()` :1335
- `_detect_global_declarations()` :1894
- `_find_nearest_common_post_dominator()` :1972
- `_find_merge_via_forward_reachability()` :2033
- `_r49a_shared_sink_tail_merge()` :2133
- `_compute_merge_from_jump_targets()` :2203
- `_get_jump_forward_target()` :2452
- `_find_jump_forward_in_successors()` :2460
- `_is_reachable_bfs()` :2494
- `_find_enclosing_loop()` :2520
- `_is_post_merge_sibling_head()` :2535
- `_is_loop_exit_block()` :2572
- `_compute_in_loop_if_merge()` :2592
- `_r57e_in_loop_branch_convergence()` :2651
- `_collect_blocks_on_path()` :2790
- `_has_with_exit_call()` :2811
- `_is_single_expression_block()` :2823
- `get_block_role()` :2994
- `_annotate_all_roles()` :2997
- `_annotate_loop_structural_roles()` :3290
- `_annotate_if_structural_roles()` :3351
- `_annotate_try_except_structural_roles()` :3374
- `_assign_region_role()` :3399
- `_get_loop_region_for_block()` :3403
- `_compute_dynamic_region_score()` :3439
- `_score_merge_semantics()` :3450
- `_score_branch_compactness()` :3472
- `_score_expression_context()` :3501
- `_score_structural_nesting()` :3530
- `_score_if_body_substance()` :3554
- `_should_use_dynamic_priority()` :3591
- `_reraise_block_offsets()` :3604
- `identify_block_prefix_instructions()` :3618
- `compute_chained_compare_operands()` :3677
- `extract_dict_key_from_block()` :3741
- `_get_dominance_depth()` :3776
- `_identify_loop_regions()` :3782
- `_rebuild_block_roles_after_fake_loop_removal()` :4620
- `_cleanup_try_else_in_loop_body()` :4685
- `_detect_and_filter_conditional_recheck_fake_loops()` :4824
- `_classify_loop_type()` :4905
- `_is_while_true()` :5025
- `_clamp_loop_else_to_enclosing_try()` :5105
- `_loop_else_nop_marker()` :5150
- `_find_loop_else()` :5242
- `_is_early_return_block()` :5939
- `_is_except_handler_block()` :5965
- `_is_outer_try_except_else_block()` :5986
- `_is_except_break_exit()` :6014
- `_detect_break_continue()` :6055
- `_collect_natural_loop_body()` :6570
- `_coalesce_nop_prefix_loop_headers()` :6858
- `_is_fake_loop()` :6884
- `_is_await_polling_loop()` :6942
- `_collect_await_predecessor_chain()` :7050
- `_skip_await_poll_to_cond_block()` :7167
- `_has_body_code_before_before_with()` :7210
- `_succ_starts_with_as_target_of_current()` :7243
- `_is_with_exit_cleanup()` :7269
- `_is_with_exit_leading_to_break()` :7298
- `_find_async_with_return_path()` :7327
- `_check_jump_backward_for_break()` :7377
- `_check_return_for_break()` :7407
- `_is_with_exit_leading_to_continue()` :7435
- `_detect_with_body_return()` :7472
- `_is_return_none_block()` :7545
- `_is_trivial_block()` :7556
- `_block_exits_loop()` :7572
- `_identify_try_except_regions()` :7603
- `_coalesce_split_try_except_finally_regions()` :8995
- `_identify_empty_body_finally_regions()` :9016
- `_parse_exception_table()` :9190
- `_w13_data_stream()` :9467
- `_w13_return_kind()` :9485
- `_w13_with_associated_handler()` :9512
- `_w13_reachable_from_with_handler()` :9530
- `_w13_handler_reaches_except_check()` :9548
- `_is_w13_finally_return_exc_copy()` :9587
- `_classify_handler_type()` :9692
- `_find_actual_handler_start()` :9913
- `_classify_handler_with_cleanup()` :9975
- `_register_region_blocks()` :10061
- `_collect_handler_chain()` :10080
- `_collect_pre_check_instrs()` :10116
- `_reconstruct_except_match_expr()` :10136
- `_extract_except_handler()` :10198
- `_follow_except_chain()` :10418
- `_w11_unprotected_else_candidate()` :10506
- `_try_body_terminates_abnormally()` :10551
- `_find_try_else_blocks()` :10647
- `_find_inner_else_blocks()` :11110
- `_is_pass_or_return_none_block()` :11260
- `_is_back_edge_target()` :11282
- `_is_reachable_from()` :11289
- `_collect_finally_body_blocks()` :11307
- `_find_next_with_block()` :11609
- `_find_with_exc_entry()` :11630
- `_collect_consecutive_with_blocks()` :11680
- `_get_with_body_range()` :11691
- `_extend_with_body_end()` :11729
- `_find_with_body_end_from_successors()` :11798
- `_find_after_with_store_block()` :11819
- `_collect_with_cleanup_blocks()` :11856
- `_collect_normal_exit_cleanup()` :11887
- `_scan_before_with_instructions()` :11998
- `_find_with_exit_block()` :12013
- `_build_single_with_region()` :12119
- `_identify_with_regions()` :12282
- `_has_intermediate_body_path()` :12435
- `identify_with_orphan_instructions()` :12453
- `_collect_with_body_blocks()` :12461
- `_extract_with_items()` :12530
- `_is_except_star_framework_block()` :12701
- `_is_match_subject_block()` :12711
- `_is_literal_default_block()` :12795
- `_verify_literal_match_chain()` :12853
- `_identify_match_regions()` :12920
- `_mr_collect_pattern_store_names()` :13077
- `_mr_compute_case_body_start_indices()` :13110
- `_mr_resolve_body_entry()` :13232
- `_mr_resolve_pattern_check_chain()` :13247
- `_mr_find_case_jump_instruction()` :13291
- `_mr_resolve_or_guard_jump()` :13302
- `_mr_find_case_success_branch()` :13351
- `_mr_collect_case_body_by_offset()` :13364
- `_mr_collect_simple_body_blocks()` :13388
- `_mr_finalize_match_region()` :13413
- `_apply_or_capture_name()` :13452
- `_set_or_pattern_names()` :13460
- `_mr_bodies_are_equivalent()` :13474
- `_mr_compute_case_merge()` :13487
- `_mr_is_default_case_block()` :13498
- `_mr_collect_case_body()` :13528
- `_is_simple_match_case_block()` :13718
- `_is_wildcard_match_block()` :13844
- `_is_none_match_block()` :13926
- `_is_wildcard_match_subject()` :14035
- `_identify_nested_match_regions()` :14044
- `_collect_nested_match_region()` :14186
- `_find_nested_match_subject()` :14261
- `_collect_nested_literal_match()` :14321
- `_scan_literal_match_subjects()` :14463
- `_is_case_pattern_block()` :14621
- `_has_match_op()` :14691
- `_is_case_fail_handler()` :14697
- `_is_implicit_default_body()` :14733
- `_is_pattern_fail_handler()` :14771
- `_identify_assert_regions()` :14799
- `_detect_assert_boolop_chain()` :15133
- `_reach_assertion_error_block()` :15342
- `_find_assertion_error_block()` :15390
- `_reaches_block_via_fallthrough()` :15439
- `_reach_raise_varargs_block()` :15470
- `_identify_chained_compare_regions()` :15495
- `_should_skip_block_for_if_region()` :15632
- `_identify_conditional_regions()` :15981
- `_resolve_boolop_condition_region()` :18180
- `_build_basic_if_region()` :18200
- `_build_elif_region()` :18719
- `_build_chained_compare_region()` :20243
- `_is_chained_compare_header()` :20411
- `_detect_chained_compare_pattern()` :20434
- `_chain_compare_op_str()` :20500
- `_identify_ternary_regions()` :20515
- `_is_block_in_region_body()` :23414
- `_identify_boolop_regions()` :23420
- `_detect_while_condition_boolop_chain()` :23938
- `_is_fused_ternary_false_value_block()` :24205
- `_detect_while_boolop_forward_chain()` :24317
- `_detect_boolop_chain_start()` :24388
- `_boolop_resolve_merge()` :24486
- `_boolop_check_condition_context()` :24631
- `_boolop_expand_non_condition_blocks()` :24653
- `_normalize_none_check_op_types()` :24678
- `_create_boolop_region_from_chain()` :24796
- `_detect_boolop_conditional_chain()` :25183
- `_is_nested_if_else_pattern()` :26690
- `_is_valid_2elem_mixed_chain()` :26767
- `_try_unify_mixed_boolop_chain()` :26797
- `_detect_boolop_short_circuit_chain()` :26816
- `_25b_then_arm_orphan_return_none()` :27017
- `_if_arm_is_sink()` :27077
- `_value_merge_hosts_next_if()` :27106
- `_conditional_value_producing_arms()` :27161
- `_ternary_merge_hosts_next_if()` :27188
- `_collect_branch_blocks()` :27214
- `_w14_pred_is_child_structural_exit()` :27423
- `_get_enclosing_structural_boundary_stop()` :27466
- `_identify_sequence_regions()` :27519
- `_get_region_offset_range()` :27632
- `_build_region_hierarchy()` :27635
- `_find_enclosing_region()` :27859
- `_is_only_jumps()` :27907
- `_is_equivalent_exit_block()` :27916
- `_is_chained_compare_cleanup_block()` :27951
- `_get_effective_merge_through_cleanup()` :27957
- `_is_trivial_return_block()` :27976
- `_is_exit_like_block()` :27995
- `get_region_for_block()` :28014
- `get_entry_region_for_block()` :28017
- `find_enclosing_region()` :28052
- `_compute_generator_entry_metadata()` :28063
- `find_generator_resume_block()` :28135
- `_precompute_all_generator_data()` :28153
- `_precompute_loop_analysis_data()` :28170
- `_precompute_chained_compare_analysis()` :28203
- `_precompute_break_jump_classification()` :28254
- `_enhance_finally_copy_annotation()` :28311

## 相关页面

- [[core-cfg-region-analyzer|core/cfg/region_analyzer.py]]
- [[index|Wiki Index]]
