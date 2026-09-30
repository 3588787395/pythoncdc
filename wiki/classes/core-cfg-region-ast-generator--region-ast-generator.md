---
type: entity
title: RegionASTGenerator
tags:
  - code-kb
related:
  - "[[core-cfg-region-ast-generator]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/region_ast_generator.py
content_hash: eda93ac4a017be57a77dbdca9e8420d9
class: RegionASTGenerator
defined_at: core/cfg/region_ast_generator.py:252
class_lines: 51488
method_count: 248
bases: []
sources:
  - core/cfg/region_ast_generator.py
---

# RegionASTGenerator

定义于 `core/cfg/region_ast_generator.py:252`（类体 51488 行，248 个方法），所属模块 [[core-cfg-region-ast-generator]]。

## 继承与 override

- 无基类（模块内独立定义）

## 机制速览

- **职责**：区域归约生成侧（S5–S7）。入口 `generate()`（`core/cfg/region_ast_generator.py:252` 类定义起点，`generate_ast_from_regions()` 在 `:51743`）消费 `RegionAnalyzer` 产出的区域树，产出 AST dict，交给 `CFGASTConverter`。
- **文件顶部已有模块级纯函数先例**（`_negate_expr` `:46`、`_flip_is_none_compare` `:62`、`_flip_contains_compare` `:88`、`_fallthrough_cond_for_jump` `:105`、`_cleanup_epilogue_pops` `:172`、`_is_duplicated_cleanup_exit_return` `:185`、`_r61_is_pure_jump_stub` `:213`）——把纯函数移出 god class 的可行模板。
- **负担集中**：S5 占本类 33,179 行（65%）；前 3 大方法各读 32–44 个实例字段（`_generate_block_statements_body` 4,022 行读 42、`_generate_ternary` 3,639 行读 44、`_process_if_blocks` 1,696 行读 32）。
- **桥接职责**：内部区域被过滤时产生的孤儿块在此释放（见 [[region-reduction-internals]] §7.1）。
- **深度阅读**：[[region-reduction-internals]]。

## 方法清单

- `__init__()` :270
- `block_role()` :333
- `_split_block_condition_prefix()` :336
- `_instruction_stack_effect()` :427
- `_collect_assert_prefix_stmts()` :443
- `_take_assert_prefix_stmts()` :463
- `_extract_imports_from_block_prefix()` :468
- `_normalize_stmt_lists()` :611
- `_normalize_stmt_node()` :635
- `generate()` :672
- `_detect_docstring_statement()` :1921
- `_build_function_def()` :1963
- `_extract_decorators()` :2312
- `_reconstruct_decorator_chain()` :2434
- `_split_subscr_operands()` :2655
- `_detect_walrus_prefix()` :2719
- `_build_walrus_assign()` :2746
- `_build_effective_stmts()` :2787
- `_build_class_def()` :2914
- `_extract_function_args()` :3065
- `_generate_degraded_statements()` :3156
- `_generate_region()` :3188
- `_generate_assert()` :3431
- `_invert_assert_none_check_direction()` :3709
- `_build_assert_chained_compare()` :3761
- `_build_assert_boolop_condition()` :3883
- `_resolve_assert_message_ternary_expr()` :3992
- `_build_assert_message()` :4087
- `_generate_loop()` :4151
- `_loop_generate_for()` :4458
- `_r58_collect_break_target_stmts()` :5160
- `_loop_generate_while()` :5230
- `_loop_generate_body()` :6794
- `_loop_collect_child_regions()` :7036
- `_loop_generate_pre_stmts()` :7080
- `_is_for_iter_setup_of_ungenerated_loop()` :7105
- `_loop_extract_for_iter_pre_stmts()` :7138
- `_loop_extract_pre_stmts_from_block()` :7326
- `_loop_dispatch_block()` :7398
- `_loop_handle_header()` :7723
- `_reconstruct_await_block_stmts()` :8394
- `_fallthrough_successor_excluding()` :8487
- `_loop_extract_self_loop_stmts()` :8516
- `_generate_elif_else_chain()` :9514
- `_loop_handle_header_no_condition()` :9585
- `_loop_handle_boolop_or_if_header()` :9756
- `_loop_process_header_instructions()` :9809
- `_loop_process_header_break_condition()` :10005
- `_loop_handle_exit_successors()` :10077
- `_block_is_continue_target()` :10289
- `_is_loop_tail_convergence_block()` :10302
- `_block_is_pure_continue()` :10342
- `_is_with_exit_back_edge()` :10360
- `_loop_handle_no_exit_successors()` :10389
- `_fold_header_then_continuation()` :10597
- `_loop_build_if_with_exit_branches()` :10693
- `_loop_process_natural_back_edge()` :10865
- `_loop_find_cond_start_idx()` :10919
- `_loop_extract_pre_stmts_from_instrs()` :11015
- `_loop_handle_continue()` :11131
- `_loop_handle_back_edge()` :11146
- `_loop_process_back_edge_with_condition()` :11269
- `_loop_handle_child_region_entry()` :11333
- `_loop_postprocess()` :11628
- `_generate_if()` :11742
- `_detect_if_region_as_while_loop()` :11960
- `_build_while_combined_condition()` :12095
- `_generate_value_context_chain_compare_assign()` :12153
- `_extract_vc_pre_store_statements()` :12387
- `_build_chained_compare_with_ternary_middle()` :12434
- `_if_generate_full_elif_chain()` :12515
- `_build_chained_compare_from_region_data()` :13486
- `_try_build_walrus_chained_compare()` :13555
- `_try_build_literal_middle_chained_compare()` :13729
- `_try_build_method_call_chained_compare()` :13739
- `_try_build_literal_middle_from_blocks()` :13867
- `_try_build_call_middle_from_blocks()` :13966
- `_try_build_call_middle_chained_compare()` :14086
- `_try_build_attr_middle_chained_compare()` :14096
- `_try_build_attr_middle_from_blocks()` :14133
- `_try_build_complex_operand_chained_compare_from_blocks()` :14232
- `_detect_boolop_after_chained_compare()` :14376
- `_if_extract_cond_instructions()` :14477
- `_expr_child_blocked_by_structural_sibling()` :14990
- `_if_generate_then_branch()` :15032
- `_if_generate_else_branch()` :15670
- `_else_blocks_exit_enclosing_loop()` :16017
- `_is_chained_compare_cleanup_else()` :16050
- `_is_implicit_return_block()` :16071
- `_r23n16_blocks_have_explicit_return()` :16080
- `_if_generate_elif_chain()` :16103
- `_extract_condition_for_elif_block()` :17272
- `_cond_block_branch_targets()` :17326
- `_condition_chain_targets_consistent()` :17358
- `_merge_block_is_then_exclusive()` :17406
- `_chain_block_condition_instrs()` :17557
- `_chain_block_is_pure()` :17571
- `_generate_chain_head_prefix_assign()` :17589
- `_discover_predicate_and_chain()` :17675
- `_discover_predicate_and_chain_forward()` :17819
- `_boolop_merge_owner_for()` :17887
- `_if_generate_normal()` :17949
- `_try_build_await_condition()` :19257
- `_try_build_await_boolop_operand()` :19436
- `_extract_trapped_lhs_from_ternary()` :19520
- `_extract_pre_ternary_instrs()` :19564
- `_build_simple_load()` :19607
- `_sim_wrapping_instr()` :19618
- `_binary_op_arg_to_str()` :19998
- `_flatten_dict_merge_to_keywords()` :20016
- `_build_ternary_wrapped_expr()` :20056
- `_build_compare_ternary_condition()` :20228
- `_then_entry_offsets_excluding_connectors()` :20361
- `_block_is_structural_for_iter_exit()` :20417
- `_block_is_pure_back_edge_to_header()` :20444
- `_block_is_child_loop_natural_backedge()` :20475
- `_if_false_path_is_loop_iteration()` :20557
- `_handler_backedge_is_natural_loop_iteration()` :20590
- `_handler_backedge_is_explicit_continue()` :20632
- `_if_extract_condition_from_instructions()` :20669
- `_convert_lambda_function_objects()` :21376
- `_build_boolop_condition_from_chain()` :21431
- `_try_generate_await_list_assign()` :21552
- `_break_block_is_chain_compare_loop_exit()` :21721
- `_process_if_blocks()` :21776
- `_try_generate_conditional_break()` :23473
- `_try_generate_conditional_break_or_continue()` :23627
- `_is_child_reachable_from_blocks()` :24451
- `_if_generate_branch_stmts()` :24475
- `_coalesce_compares()` :24483
- `_generate_try_body()` :24522
- `_w13_data_stream()` :25658
- `_is_w13_single_return_normal_copy()` :25676
- `_count_nested_try_marker_levels()` :25743
- `_find_finally_normal_copy_blocks()` :25786
- `_generate_try()` :26128
- `_find_return_chain_via_successors()` :27629
- `_find_return_through_cleanup_chain()` :27730
- `_generate_handler_body_statements()` :27789
- `_rag_is_orphan_nop_statement()` :28780
- `_build_statements_from_instructions()` :28845
- `_mark_with_cleanup_generated()` :29274
- `_generate_class_body_from_code()` :29277
- `_filter_if_blocks_in_with()` :29296
- `_extract_return_from_exit_block()` :29381
- `_extract_async_with_return_value()` :29395
- `_resolve_nested_ternary_context_expr()` :29418
- `_generate_with()` :29490
- `_generate_match()` :30793
- `_detect_undetected_wildcard_match()` :31601
- `_collect_guard_pattern_blocks()` :31699
- `_compute_body_block_start()` :31769
- `_collect_pattern_store_names()` :31816
- `_wrap_boolop_with_merge_compare()` :31849
- `_try_build_chained_compare_in_boolop()` :32093
- `_try_build_nested_ternary_in_boolop()` :32216
- `_detect_boolop_grouping()` :32306
- `_build_grouped_boolop_expression()` :32379
- `_build_boolop_expression()` :32662
- `_try_build_and_inner_or_pattern()` :33178
- `_reconstruct_boolop_operand()` :33285
- `_build_boolop_augassign_target()` :33307
- `_r4e_else_target_is_join()` :33400
- `_generate_boolop()` :33456
- `_generate_boolop_impl()` :33487
- `_build_ternary_boolop_condition()` :34856
- `_build_simple_ternary_value()` :34953
- `_build_ternary_value_expr()` :34978
- `_build_nested_ternary_expr()` :35047
- `_try_build_ternary_boolop_and_if()` :35084
- `_merge_block_is_loop_back_edge()` :35352
- `_ternary_nested_in_container_construction()` :35365
- `_generate_container_construction_region()` :35417
- `_try_build_andor_boolop_from_ternary()` :35457
- `_r63b3_is_chain_cleanup_arm()` :35575
- `_r63b3_reduce_value_ctx_chain_store()` :35612
- `_r67_split_cc_ternary_stmt_prefix()` :35704
- `_generate_ternary()` :35757
- `_try_build_ternary_as_if_cond()` :39397
- `_try_build_nested_ternary_as_if_cond()` :39585
- `_compute_ternary_cond_preload_exprs()` :39736
- `_split_preload_into_siblings()` :39884
- `_split_raise_from_stmts()` :39935
- `_stack_effect()` :39983
- `_collect_post_ternary_positional_args()` :40032
- `_emit_post_extra_with_if_upgrade()` :40067
- `_build_ternary_no_target_consumer_stmt()` :40197
- `_build_assert_message_ternary_stmt()` :40646
- `_try_build_ternary_store_assign()` :40777
- `_build_multi_target_del_targets()` :41365
- `_build_ternary_augassign_subscr_target()` :41454
- `_build_ternary_augassign_attr_target()` :41517
- `_extract_cond_preload_value_expr()` :41581
- `_try_build_ternary_comprehension_iter()` :41650
- `_try_build_ternary_chained_compare()` :41759
- `_try_build_ternary_merge_consumer_expr()` :41945
- `_try_build_chained_ternary_make_function()` :42324
- `_extract_dict_prefix_values()` :42407
- `_ternary_prefix_stack_effect()` :42498
- `_r64b1_fv_conversion()` :42534
- `_fstring_parts_from_segment()` :42563
- `_ternary_pending_callee()` :42613
- `_try_wrap_fstring_pending_call()` :42744
- `_try_build_ternary_chained_container()` :42820
- `_try_build_ternary_chained_pattern()` :43499
- `_try_build_ternary_kwarg_call()` :44254
- `_is_orphan_boundary_nop()` :44419
- `_generate_basic_region()` :44529
- `_w16_split_value_groups()` :44602
- `_loop_exit_is_implicit_return_none()` :44704
- `_with_jump_exit_blocks()` :44758
- `_downstream_region_entry()` :44788
- `_mark_with_exit_return_explicit()` :44832
- `_mark_shared_return_explicit()` :44860
- `_generate_block_statements()` :44902
- `_generate_block_statements_body()` :44955
- `_apply_r23n6_return_promotion()` :48978
- `_find_await_store_target()` :49041
- `_is_mangled_name()` :49092
- `_safe_set_func_name()` :49100
- `_process_instruction()` :49108
- `_build_delete_stmt()` :49224
- `_reconstruct_delete_target()` :49333
- `_generate_stmts_from_instrs()` :49411
- `_is_statement_reduction_entry()` :49765
- `_build_unpack_assign_from_segment()` :49784
- `_register_prefix_emitted()` :49821
- `_build_prefix_stmt_list()` :49845
- `_reconstruct_raise_exc()` :49934
- `_build_raise_stmt_from_instrs()` :49986
- `_build_statement()` :50001
- `_build_attr_target_unpack()` :50086
- `_build_multi_target_unpack()` :50218
- `_build_store_statement()` :50293
- `_build_subscript_assign()` :50540
- `_is_type_like_expr()` :50780
- `_is_type_like_slice()` :50798
- `_try_build_ann_assign_complex_target()` :50807
- `_build_attr_assign()` :50911
- `_is_trailing_return_none_statement()` :51205
- `_filter_module_level_returns()` :51220
- `_is_loop_break_return()` :51250
- `_block_has_fallthrough_predecessor()` :51267
- `_w14_has_following_code()` :51300
- `_w14_join_bare_return_none()` :51328
- `_w14_explicit_return_flag()` :51369
- `_try_deferred_return_in_loop()` :51410
- `_generate_return_ast()` :51618

## 相关页面

- [[core-cfg-region-ast-generator|core/cfg/region_ast_generator.py]]
- [[index|Wiki Index]]
