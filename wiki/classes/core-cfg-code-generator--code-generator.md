---
type: entity
title: CodeGenerator
tags:
  - code-kb
related:
  - "[[core-cfg-code-generator]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/code_generator.py
content_hash: 7dd6b89716aced187f97513609cbb67c
class: CodeGenerator
defined_at: core/cfg/code_generator.py:44
class_lines: 5905
method_count: 127
bases: []
sources:
  - core/cfg/code_generator.py
---

# CodeGenerator

定义于 `core/cfg/code_generator.py:44`（类体 5905 行，127 个方法），所属模块 [[core-cfg-code-generator]]。

> CFG代码生成器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :52
- `generate()` :94
- `_in_function_context()` :128
- `_is_in_if_body()` :132
- `_indent()` :136
- `_write()` :140
- `_write_line()` :147
- `_increase_indent()` :153
- `_decrease_indent()` :157
- `_generate_node()` :161
- `_generate_dict_node()` :239
- `_generate_aug_assign_dict()` :452
- `_generate_function_def_dict()` :467
- `_generate_arguments_dict()` :536
- `_is_simple_stmt()` :620
- `_is_simple_single_statement()` :628
- `_generate_single_stmt_line()` :639
- `_generate_try_dict()` :649
- `_generate_with_dict()` :808
- `_generate_delete_dict()` :858
- `_generate_if_dict()` :886
- `_generate_elif_or_else_dict()` :965
- `_generate_return_dict()` :1012
- `_generate_assign_dict()` :1021
- `_generate_aug_assign_dict()` :1161
- `_generate_ann_assign_dict()` :1181
- `_generate_for_dict()` :1195
- `_generate_while_dict()` :1247
- `_generate_block()` :1280
- `_generate_if()` :1285
- `_filter_duplicate_if_in_else()` :1488
- `_get_condition_str()` :1542
- `_get_operand_str()` :1558
- `_test_is_simple_variable()` :1568
- `_detect_compound_condition()` :1577
- `_get_last_if_in_compound()` :1677
- `_generate_elif_or_else()` :1708
- `_generate_for()` :1832
- `_generate_for_target()` :1873
- `_generate_for_target_from_dict()` :1903
- `_is_only_return_none()` :1935
- `_generate_while()` :1964
- `_generate_try()` :2023
- `_generate_except_handler()` :2063
- `_generate_with()` :2108
- `_generate_with_item()` :2130
- `_generate_function_def()` :2142
- `_filter_trailing_return_none()` :2218
- `_generate_lambda_expr()` :2347
- `_generate_node_code()` :2375
- `_generate_decorator()` :2395
- `_filter_return_nodes()` :2458
- `_filter_class_internal_assigns()` :2481
- `_generate_class_def()` :2542
- `_generate_class_def_dict()` :2607
- `_generate_return()` :2645
- `_generate_yield()` :2671
- `_generate_assign()` :2679
- `_fold_constant_expression()` :2850
- `_generate_aug_assign()` :2933
- `_generate_ann_assign()` :2953
- `_generate_expr_stmt()` :2974
- `_generate_pass()` :3043
- `_generate_break()` :3047
- `_generate_continue()` :3058
- `_node_contains_break()` :3066
- `_generate_delete_node()` :3080
- `_generate_raise()` :3100
- `_generate_assert()` :3128
- `_generate_global()` :3140
- `_generate_nonlocal()` :3145
- `_generate_match()` :3152
- `_generate_case()` :3202
- `_generate_match_pattern()` :3240
- `_generate_import()` :3376
- `_generate_import_from()` :3392
- `_generate_expression()` :3411
- `_generate_constant()` :3914
- `_decompile_nested_code()` :3978
- `_wrap_function_def()` :4038
- `_generate_binary()` :4075
- `_generate_unary()` :4155
- `_get_ast_expr_precedence()` :4180
- `_generate_compare()` :4229
- `_generate_call()` :4267
- `_generate_attribute()` :4332
- `_generate_subscript()` :4355
- `_generate_subscript_annotation()` :4392
- `_generate_annotation_from_node()` :4409
- `_generate_slice_in_subscript()` :4437
- `_generate_slice()` :4456
- `_generate_slice_as_function_call()` :4468
- `_generate_slice_as_call()` :4520
- `_generate_list()` :4564
- `_generate_tuple()` :4570
- `_generate_dict()` :4584
- `_generate_set()` :4595
- `_generate_joined_str_from_dict()` :4606
- `_generate_formatted_value_from_dict()` :4672
- `_generate_format_spec_inner_from_dict()` :4714
- `_generate_joined_str()` :4742
- `_generate_formatted_value()` :4810
- `_generate_list_comp()` :4845
- `_generate_set_comp()` :4873
- `_generate_dict_comp()` :4884
- `_generate_gen_expr()` :4896
- `_generate_list_comp_from_dict()` :4909
- `_generate_slice_from_dict()` :4935
- `_generate_lambda_from_dict()` :4948
- `_generate_set_comp_from_dict()` :4975
- `_generate_match_case_dict()` :4991
- `_generate_dict_comp_from_dict()` :5032
- `_generate_gen_expr_from_dict()` :5054
- `_generate_comprehensions_from_dict()` :5070
- `_generate_named_expr()` :5153
- `_generate_ifexp()` :5168
- `_get_dict_expr_precedence()` :5192
- `_generate_binop_from_dict()` :5221
- `_generate_ifexp_from_dict()` :5253
- `_generate_boolop_from_dict()` :5278
- `_generate_unaryop_from_dict()` :5306
- `_generate_compare_from_dict()` :5342
- `_generate_awaitable()` :5404
- `_generate_lambda_expr()` :5430
- `_generate_comprehensions()` :5451
- `_generate_annotation_from_dict()` :5527
- `_generate_arguments()` :5769

## 相关页面

- [[core-cfg-code-generator|core/cfg/code_generator.py]]
- [[index|Wiki Index]]
