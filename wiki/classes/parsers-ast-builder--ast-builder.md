---
type: entity
title: ASTBuilder
tags:
  - code-kb
related:
  - "[[parsers-ast-builder]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: parsers/ast_builder.py
content_hash: ed1d227dad5ef67f35e0d5e0d0ce9bc6
class: ASTBuilder
defined_at: parsers/ast_builder.py:1060
class_lines: 29205
method_count: 231
bases: []
sources:
  - parsers/ast_builder.py
---

# ASTBuilder

定义于 `parsers/ast_builder.py:1060`（类体 29205 行，231 个方法），所属模块 [[parsers-ast-builder]]。

> AST构建器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :1066
- `_get_chained_compare_state()` :1195
- `_set_chained_compare_state()` :1201
- `build_from_code()` :1209
- `_get_instr_name()` :2095
- `_prescan_for_loops()` :2103
- `_pop_blocks_to_current_pos()` :2548
- `_push_block()` :2583
- `_pop_block_from_stack()` :2588
- `_emit_pending_assignments()` :2596
- `_emit()` :2767
- `_find_else_end()` :5222
- `_find_else_end_wrapper()` :6381
- `_process_instruction()` :6386
- `_unary_op()` :7467
- `_list_append()` :7476
- `_dict_merge()` :7489
- `_set_update()` :7519
- `_is_op()` :7549
- `_contains_op()` :7562
- `_detect_exception_var()` :7575
- `_check_exc_match()` :7687
- `_find_pop_except_in_range()` :7855
- `_is_in_exception_cleanup()` :7883
- `_check_eg_match()` :8006
- `_prep_reraise_star()` :8037
- `_pop_except()` :8060
- `_end_finally()` :8341
- `_reraise()` :8372
- `_call_intrinsic_2()` :8382
- `_load_global()` :8389
- `_store_global()` :8417
- `_get_name_from_code_obj()` :8438
- `_delete_global()` :8475
- `_delete_name()` :8481
- `_delete_fast()` :8512
- `_is_exception_var_delete()` :8545
- `_delete_subscr()` :8597
- `_store_subscr()` :8613
- `_make_cell()` :8649
- `_load_closure()` :8658
- `_load_deref()` :8744
- `_copy_free_vars()` :8822
- `_store_deref()` :8829
- `_for_iter()` :8912
- `_is_if_related_to_for_loop()` :9371
- `_condition_contains_name()` :9402
- `_get_iter()` :9427
- `_break_loop()` :9437
- `_continue_loop()` :9442
- `_handle_pop_block()` :9447
- `_setup_loop()` :9615
- `_build_slice()` :9653
- `_binary_subscript()` :9678
- `_get_slice_component_str()` :9703
- `_jump_backward_no_interrupt()` :9719
- `_recover_from_error()` :9724
- `_match_class()` :9746
- `_match_mapping()` :9799
- `_match_sequence()` :9822
- `_match_keys()` :9845
- `_safe_stack_access()` :9874
- `_load_attr()` :9889
- `_store_attr()` :9924
- `_delete_attr()` :9976
- `_load_const()` :10010
- `_create_function_from_code()` :10382
- `_create_function_from_python_code()` :11285
- `_create_lambda_from_code()` :11431
- `_enhance_with_defaults()` :11508
- `_pyc_code_to_python_code()` :11550
- `_create_comprehension_from_code()` :11676
- `_parse_comprehension_element()` :11822
- `_parse_dict_comprehension_element()` :12113
- `_build_expression_from_instructions()` :12311
- `_is_comprehension_code()` :12853
- `_infer_comprehension_type()` :12911
- `_extract_arg_name()` :12947
- `_extract_defaults_from_bytecode()` :12967
- `_extract_function_args()` :13126
- `_extract_function_args_from_python_code()` :13261
- `_extract_defaults()` :13305
- `_load_name()` :13436
- `_load_fast()` :13470
- `_store_name()` :13520
- `_store_fast()` :14687
- `_emit_pending_chain_assign()` :16258
- `_unpack_sequence()` :16304
- `_unpack_ex()` :16402
- `_binary_op()` :16473
- `_compare_op()` :16559
- `_return_value()` :16592
- `_yield_value()` :16970
- `_update_comprehension_iter()` :17071
- `_call_function()` :17094
- `_call_function_ex()` :17551
- `_parse_annotation_tuple()` :17642
- `_make_function()` :17696
- `_build_class()` :17993
- `_create_class_from_code()` :18060
- `_create_class_from_python_code()` :18593
- `_process_module_level_functions()` :18841
- `_build_function_ast()` :18959
- `_build_class_body_from_code()` :19033
- `_build_from_python_code()` :19152
- `_build_from_python_code_with_cfg()` :19243
- `_build_from_python_code_traditional()` :19335
- `_convert_cfg_ast_to_project_ast()` :19394
- `_convert_cfg_node()` :19423
- `_process_python_code()` :19602
- `_build_class_body_from_native_code()` :19690
- `_build_list()` :19722
- `_build_tuple()` :19736
- `_build_set()` :19750
- `_build_map()` :19764
- `_build_const_key_map()` :19802
- `_list_extend()` :19875
- `_set_add()` :19948
- `_dict_update()` :19964
- `_map_add()` :19977
- `_pop_top()` :19994
- `_dup_top()` :20336
- `_rot_two()` :20342
- `_rot_three()` :20355
- `_swap()` :20371
- `_is_chain_compare_pattern()` :20482
- `_copy()` :20552
- `_kw_names()` :20629
- `_precall_a()` :20700
- `_store_global()` :20713
- `_delete_global()` :20762
- `_pop_jump_if_false()` :20777
- `_get_instruction_at_offset()` :21431
- `_get_instruction_before_offset()` :21443
- `_get_instruction_after_offset()` :21461
- `_is_in_exception_context()` :21474
- `_pop_jump_forward_if_true()` :21514
- `_is_assert_pattern()` :21798
- `_pop_jump_backward_if_true()` :21846
- `_pop_jump_forward_if_false()` :21919
- `_pop_jump_backward_if_false()` :24739
- `_is_break_pattern()` :24773
- `_jump_forward()` :24808
- `_jump_if_false_or_pop()` :25181
- `_is_chain_compare_jump()` :25218
- `_jump_if_true_or_pop()` :25264
- `_is_logical_expression_jump()` :25287
- `_is_loop_jump()` :25317
- `_is_break_jump()` :25326
- `_is_continue_jump()` :25560
- `_is_in_loop_body()` :25640
- `_find_loop_at_target()` :25657
- `_create_conditional_branch()` :25665
- `_build_string()` :25703
- `_load_global()` :25716
- `_load_build_class()` :25764
- `_get_current_names()` :25771
- `_get_module_level_names()` :25793
- `_import_name()` :25824
- `_process_import_name()` :25877
- `_import_from()` :25986
- `_generate_temp_var()` :26046
- `_get_name_from_index()` :26054
- `_break_loop()` :26075
- `_raise_varargs()` :26080
- `_setup_except()` :26336
- `_setup_finally()` :26436
- `_setup_with()` :26464
- `_before_with()` :26637
- `_before_async_with()` :27132
- `_push_exc_info()` :27174
- `_is_try_except_pattern()` :28310
- `_check_if_finally_block()` :28731
- `_is_real_finally_block()` :28956
- `_move_finally_code_from_try_block()` :29025
- `_jump_backward_no_interrupt()` :29073
- `_is_while_loop()` :29085
- `_build_control_flow_edge()` :29104
- `_analyze_control_flow_pattern()` :29164
- `_pop_jump_forward_if_none()` :29291
- `_pop_jump_forward_if_not_none()` :29344
- `_handle_if_structure()` :29404
- `_handle_for_loop()` :29420
- `_handle_while_loop()` :29426
- `_handle_try_except()` :29432
- `_create_exception_handler()` :29447
- `_extract_decorators()` :29468
- `_safe_stack_pop()` :29476
- `_safe_stack_top()` :29488
- `_create_unary_op()` :29497
- `_create_compare_op()` :29507
- `_handle_jump_instruction()` :29515
- `_complete_control_flow_structures()` :29537
- `_complete_while_loop()` :29546
- `_complete_for_loop()` :29552
- `_handle_block_management()` :29558
- `_process_exception_block()` :29571
- `_create_jump_target()` :29577
- `_extract_function_defaults()` :29587
- `_convert_constant_to_ast()` :29608
- `_optimize_ast_structure()` :29627
- `_finalize_ast()` :29637
- `_set_parent_child_relationships()` :29647
- `get_control_flow_graph()` :29655
- `get_loop_structures()` :29659
- `get_exception_blocks()` :29663
- `get_branch_patterns()` :29667
- `get_unreachable_blocks()` :29671
- `_list_append()` :29677
- `_dict_merge()` :29690
- `_set_update()` :29720
- `_is_op()` :29726
- `_contains_op()` :29739
- `_call_intrinsic_2()` :29759
- `_load_method()` :29766
- `_load_global()` :29791
- `_store_global()` :29816
- `_delete_global()` :29866
- `_format_value()` :29872
- `_build_string()` :29899
- `_break_loop()` :29917
- `_continue_loop()` :29922
- `_load_name()` :29928
- `_enhanced_build()` :29987
- `_parse_instructions_intelligently()` :30027
- `_build_function_ast()` :30157
- `_extract_string_value()` :30203
- `_fallback_build()` :30213
- `_load_assertion_error()` :30239
- `_return_generator()` :30246
- `_yield_from()` :30253

## 相关页面

- [[parsers-ast-builder|parsers/ast_builder.py]]
- [[index|Wiki Index]]
