---
type: entity
title: ASTBuilder
tags:
  - code-kb
related:
  - "[[parsers-ast-builder-cleaned]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: parsers/ast_builder_cleaned.py
content_hash: 26256f36b353d6a4ebcd9557fad4df1a
class: ASTBuilder
defined_at: parsers/ast_builder_cleaned.py:1060
class_lines: 28420
method_count: 229
bases: []
sources:
  - parsers/ast_builder_cleaned.py
---

# ASTBuilder

定义于 `parsers/ast_builder_cleaned.py:1060`（类体 28420 行，229 个方法），所属模块 [[parsers-ast-builder-cleaned]]。

> AST构建器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :1066
- `_get_chained_compare_state()` :1197
- `_set_chained_compare_state()` :1203
- `build_from_code()` :1211
- `_get_instr_name()` :2108
- `_prescan_for_loops()` :2116
- `_pop_blocks_to_current_pos()` :2561
- `_push_block()` :2596
- `_pop_block_from_stack()` :2601
- `_emit_pending_assignments()` :2609
- `_emit()` :2780
- `_find_else_end()` :5233
- `_find_else_end_wrapper()` :6392
- `_process_instruction()` :6397
- `_unary_op()` :7475
- `_list_append()` :7484
- `_dict_merge()` :7497
- `_set_update()` :7527
- `_is_op()` :7556
- `_contains_op()` :7569
- `_detect_exception_var()` :7582
- `_check_exc_match()` :7694
- `_find_pop_except_in_range()` :7862
- `_is_in_exception_cleanup()` :7890
- `_check_eg_match()` :8013
- `_prep_reraise_star()` :8044
- `_pop_except()` :8067
- `_end_finally()` :8349
- `_reraise()` :8380
- `_call_intrinsic_2()` :8390
- `_load_global()` :8397
- `_store_global()` :8425
- `_get_name_from_code_obj()` :8446
- `_delete_global()` :8483
- `_delete_name()` :8489
- `_delete_fast()` :8520
- `_is_exception_var_delete()` :8553
- `_delete_subscr()` :8605
- `_store_subscr()` :8621
- `_make_cell()` :8657
- `_load_closure()` :8666
- `_load_deref()` :8676
- `_copy_free_vars()` :8754
- `_store_deref()` :8761
- `_for_iter()` :8844
- `_is_if_related_to_for_loop()` :9303
- `_condition_contains_name()` :9334
- `_get_iter()` :9359
- `_break_loop()` :9369
- `_continue_loop()` :9374
- `_handle_pop_block()` :9379
- `_setup_loop()` :9547
- `_build_slice()` :9585
- `_binary_subscript()` :9610
- `_get_slice_component_str()` :9635
- `_jump_backward_no_interrupt()` :9651
- `_recover_from_error()` :9656
- `_match_class()` :9678
- `_match_mapping()` :9731
- `_match_sequence()` :9754
- `_match_keys()` :9777
- `_safe_stack_access()` :9806
- `_load_attr()` :9821
- `_store_attr()` :9856
- `_delete_attr()` :9901
- `_load_const()` :9935
- `_create_function_from_code()` :10306
- `_create_function_from_python_code()` :11208
- `_enhance_with_defaults()` :11350
- `_pyc_code_to_python_code()` :11392
- `_create_comprehension_from_code()` :11518
- `_parse_comprehension_element()` :11664
- `_parse_dict_comprehension_element()` :11936
- `_build_expression_from_instructions()` :12134
- `_is_comprehension_code()` :12500
- `_infer_comprehension_type()` :12558
- `_extract_arg_name()` :12594
- `_extract_defaults_from_bytecode()` :12614
- `_extract_function_args()` :12773
- `_extract_function_args_from_python_code()` :12908
- `_extract_defaults()` :12952
- `_load_name()` :13083
- `_load_fast()` :13117
- `_store_name()` :13167
- `_store_fast()` :14310
- `_emit_pending_chain_assign()` :15858
- `_unpack_sequence()` :15904
- `_unpack_ex()` :16002
- `_binary_op()` :16073
- `_compare_op()` :16159
- `_return_value()` :16192
- `_yield_value()` :16581
- `_update_comprehension_iter()` :16676
- `_call_function()` :16699
- `_call_function_ex()` :17077
- `_make_function()` :17168
- `_build_class()` :17436
- `_create_class_from_code()` :17503
- `_create_class_from_python_code()` :17999
- `_process_module_level_functions()` :18209
- `_build_function_ast()` :18328
- `_build_class_body_from_code()` :18402
- `_build_from_python_code()` :18521
- `_build_from_python_code_with_cfg()` :18612
- `_build_from_python_code_traditional()` :18704
- `_convert_cfg_ast_to_project_ast()` :18763
- `_convert_cfg_node()` :18792
- `_process_python_code()` :18870
- `_build_class_body_from_native_code()` :18958
- `_build_list()` :18990
- `_build_tuple()` :19004
- `_build_set()` :19018
- `_build_map()` :19032
- `_build_const_key_map()` :19070
- `_list_extend()` :19143
- `_set_add()` :19216
- `_dict_update()` :19232
- `_map_add()` :19245
- `_pop_top()` :19262
- `_dup_top()` :19588
- `_rot_two()` :19594
- `_rot_three()` :19607
- `_swap()` :19623
- `_is_chain_compare_pattern()` :19719
- `_copy()` :19789
- `_kw_names()` :19867
- `_precall_a()` :19938
- `_store_global()` :19951
- `_delete_global()` :20000
- `_pop_jump_if_false()` :20015
- `_get_instruction_at_offset()` :20664
- `_get_instruction_before_offset()` :20676
- `_get_instruction_after_offset()` :20694
- `_is_in_exception_context()` :20707
- `_pop_jump_forward_if_true()` :20747
- `_is_assert_pattern()` :21034
- `_pop_jump_backward_if_true()` :21082
- `_pop_jump_forward_if_false()` :21155
- `_pop_jump_backward_if_false()` :23943
- `_is_break_pattern()` :23977
- `_jump_forward()` :24012
- `_jump_if_false_or_pop()` :24384
- `_is_chain_compare_jump()` :24421
- `_jump_if_true_or_pop()` :24467
- `_is_logical_expression_jump()` :24490
- `_is_loop_jump()` :24520
- `_is_break_jump()` :24529
- `_is_continue_jump()` :24763
- `_is_in_loop_body()` :24843
- `_find_loop_at_target()` :24860
- `_create_conditional_branch()` :24868
- `_build_string()` :24906
- `_load_global()` :24919
- `_load_build_class()` :24967
- `_get_current_names()` :24974
- `_get_module_level_names()` :24996
- `_import_name()` :25027
- `_process_import_name()` :25080
- `_import_from()` :25189
- `_generate_temp_var()` :25249
- `_get_name_from_index()` :25257
- `_break_loop()` :25278
- `_raise_varargs()` :25283
- `_setup_except()` :25539
- `_setup_finally()` :25639
- `_setup_with()` :25667
- `_before_with()` :25884
- `_before_async_with()` :26341
- `_push_exc_info()` :26383
- `_is_try_except_pattern()` :27521
- `_check_if_finally_block()` :27944
- `_is_real_finally_block()` :28171
- `_move_finally_code_from_try_block()` :28240
- `_jump_backward_no_interrupt()` :28288
- `_is_while_loop()` :28300
- `_build_control_flow_edge()` :28319
- `_analyze_control_flow_pattern()` :28379
- `_pop_jump_forward_if_none()` :28506
- `_pop_jump_forward_if_not_none()` :28559
- `_handle_if_structure()` :28619
- `_handle_for_loop()` :28635
- `_handle_while_loop()` :28641
- `_handle_try_except()` :28647
- `_create_exception_handler()` :28662
- `_extract_decorators()` :28683
- `_safe_stack_pop()` :28691
- `_safe_stack_top()` :28703
- `_create_unary_op()` :28712
- `_create_compare_op()` :28722
- `_handle_jump_instruction()` :28730
- `_complete_control_flow_structures()` :28752
- `_complete_while_loop()` :28761
- `_complete_for_loop()` :28767
- `_handle_block_management()` :28773
- `_process_exception_block()` :28786
- `_create_jump_target()` :28792
- `_extract_function_defaults()` :28802
- `_convert_constant_to_ast()` :28823
- `_optimize_ast_structure()` :28842
- `_finalize_ast()` :28852
- `_set_parent_child_relationships()` :28862
- `get_control_flow_graph()` :28870
- `get_loop_structures()` :28874
- `get_exception_blocks()` :28878
- `get_branch_patterns()` :28882
- `get_unreachable_blocks()` :28886
- `_list_append()` :28892
- `_dict_merge()` :28905
- `_set_update()` :28935
- `_is_op()` :28941
- `_contains_op()` :28954
- `_call_intrinsic_2()` :28974
- `_load_method()` :28981
- `_load_global()` :29006
- `_store_global()` :29031
- `_delete_global()` :29081
- `_format_value()` :29087
- `_build_string()` :29114
- `_break_loop()` :29132
- `_continue_loop()` :29137
- `_load_name()` :29143
- `_enhanced_build()` :29202
- `_parse_instructions_intelligently()` :29242
- `_build_function_ast()` :29372
- `_extract_string_value()` :29418
- `_fallback_build()` :29428
- `_load_assertion_error()` :29454
- `_return_generator()` :29461
- `_yield_from()` :29468

## 相关页面

- [[parsers-ast-builder-cleaned|parsers/ast_builder_cleaned.py]]
- [[index|Wiki Index]]
