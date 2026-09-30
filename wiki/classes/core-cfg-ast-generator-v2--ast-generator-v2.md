---
type: entity
title: ASTGeneratorV2
tags:
  - code-kb
related:
  - "[[core-cfg-ast-generator-v2]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/ast_generator_v2.py
content_hash: d79f62e6d3deab295fec52d22bb10ebe
class: ASTGeneratorV2
defined_at: core/cfg/ast_generator_v2.py:2681
class_lines: 24184
method_count: 93
bases: []
sources:
  - core/cfg/ast_generator_v2.py
---

# ASTGeneratorV2

定义于 `core/cfg/ast_generator_v2.py:2681`（类体 24184 行，93 个方法），所属模块 [[core-cfg-ast-generator-v2]]。

> 改进的AST生成器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :2688
- `generate()` :2706
- `_get_used_const_indices()` :3073
- `_get_unused_consts()` :3093
- `_remove_unreachable_code()` :3119
- `_has_terminal_statement()` :3158
- `_combine_multi_decorators()` :3185
- `_reconstruct_compound_condition_assignment()` :3538
- `_combine_ann_assign_with_assign()` :3670
- `_find_function_def()` :3705
- `_reconstruct_compound_conditions_in_ast()` :3731
- `_try_merge_compound_condition()` :3765
- `_build_compound_test()` :3866
- `_extract_function_args()` :3887
- `_decompile_lambda_function()` :4116
- `_decompile_comprehension()` :4177
- `_extract_multiple_comprehension_generators()` :4315
- `_extract_comprehension_ifs()` :4451
- `_extract_comprehension_element()` :4570
- `_extract_dict_comprehension_elements()` :4860
- `_generate_comprehension_function()` :5077
- `_generate_chained_compare()` :5294
- `_generate_entry_sequence()` :5459
- `_generate_block_content_skip_iterator()` :6084
- `_generate_structure()` :8310
- `_is_not_condition()` :8546
- `_generate_nop_if_ast()` :8640
- `_generate_if_ast()` :9397
- `_detect_compound_condition_in_ast()` :13336
- `_detect_compound_condition_assignment()` :13406
- `_detect_conditional_expression()` :13668
- `_generate_dict_with_ifexp()` :14384
- `_find_common_successor()` :14465
- `_instr_to_ast()` :14504
- `_extract_block_content()` :14522
- `_get_compound_body()` :14536
- `_get_compound_else_body()` :14555
- `_generate_yield_from_ast()` :14573
- `_generate_loop_ast()` :14697
- `_generate_for_loop_v2()` :14716
- `_find_structure_by_entry_block()` :15434
- `_find_if_structure_containing_block()` :15449
- `_find_if_ast_by_entry_block()` :15476
- `_extract_pre_condition_statements()` :15494
- `_generate_init_block_content()` :15681
- `_generate_while_loop_v2()` :15766
- `_generate_init_from_header()` :16362
- `_generate_if_from_block()` :16409
- `_process_if_else_branch_as_loop_body()` :16971
- `_generate_inner_while_from_block()` :17071
- `_generate_while_from_condition_block()` :17166
- `_generate_while_body_from_header()` :17338
- `_generate_try_except_ast()` :17432
- `_generate_with_ast()` :18577
- `_generate_pre_inner_with_code()` :20265
- `_generate_match_ast()` :20335
- `_generate_assert_ast()` :20381
- `_extract_match_subject()` :20589
- `_generate_case_ast()` :20606
- `_generate_match_pattern_ast()` :20638
- `_extract_pattern_from_instructions()` :20669
- `_generate_match_guard_ast()` :20835
- `_parse_resource_expr_from_instructions()` :20841
- `_reconstruct_expr_from_instructions()` :20874
- `_find_parallel_withs()` :21004
- `_filter_with_body_statements()` :21078
- `_parse_resource_expr()` :21093
- `_parse_func_name()` :21128
- `_parse_arg()` :21140
- `_extract_with_context()` :21163
- `_reconstruct_expression_from_instrs()` :21178
- `_generate_except_handler_block()` :21184
- `_generate_generic_structure()` :21631
- `_generate_block_sequence()` :21714
- `_generate_chain_assign_statement()` :21835
- `_filter_isolated_statements()` :21871
- `_is_isolated_statement()` :21891
- `_generate_instructions_content()` :21985
- `_collect_branch_blocks()` :22143
- `_generate_block_content_v2()` :22154
- `_is_orphan_nop_statement()` :22225
- `_process_instruction_sequence()` :22285
- `_is_block_in_loop()` :25913
- `_build_compound_condition_for_ifexp()` :25948
- `_extract_condition_v2()` :26008
- `_extract_iterator_v2()` :26167
- `_extract_loop_target()` :26240
- `_get_block_line()` :26406
- `_is_implicit_return_none()` :26413
- `_generate_condition_from_block()` :26425
- `_get_unprocessed_blocks()` :26449
- `_get_binary_op()` :26813
- `_get_binary_op_from_arg()` :26835

## 相关页面

- [[core-cfg-ast-generator-v2|core/cfg/ast_generator_v2.py]]
- [[index|Wiki Index]]
