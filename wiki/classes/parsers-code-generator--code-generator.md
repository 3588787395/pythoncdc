---
type: entity
title: CodeGenerator
tags:
  - code-kb
related:
  - "[[parsers-code-generator]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: parsers/code_generator.py
content_hash: cfe34762087fe8d6d177e973384d68d6
class: CodeGenerator
defined_at: parsers/code_generator.py:75
class_lines: 8598
method_count: 146
bases: [ABC]
sources:
  - parsers/code_generator.py
---

# CodeGenerator

定义于 `parsers/code_generator.py:75`（类体 8598 行，146 个方法），所属模块 [[parsers-code-generator]]。

> 代码生成器基类

## 继承与 override

- `ABC`（仓库外/未建页）

- 仓库内基类无同名方法 override

## 方法清单

- `__init__()` :78
- `increase_indent()` :110
- `decrease_indent()` :114
- `indent()` :120
- `_get_current_indent()` :124
- `_get_indent_level()` :128
- `_set_indent_level()` :132
- `set_type_annotation()` :136
- `get_type_annotation()` :140
- `add_comment()` :144
- `add_docstring()` :152
- `_emit_docstring()` :156
- `_get_inplace_op_str()` :163
- `_extract_constant_value()` :198
- `_format_constant_value()` :239
- `_extract_return_type_annotation()` :292
- `_infer_return_type_from_bytecode()` :341
- `_smart_infer_return_type()` :366
- `_add_parameter_type_annotations()` :397
- `_extract_type_annotation()` :450
- `_smart_infer_parameter_types()` :493
- `generate()` :521
- `_optimize_nodes()` :588
- `_is_useless_assign_delete()` :653
- `_get_node_signature()` :705
- `_get_value_signature()` :808
- `_is_allowed_duplicate()` :897
- `_post_process_code()` :914
- `_is_allowed_duplicate_line()` :993
- `_is_useless_line()` :1029
- `_optimize_function_body_nodes()` :1050
- `_process_single_node()` :1138
- `_generate_fallback_complete_source()` :1217
- `_generate_complete_function()` :1225
- `_generate_complete_class()` :1637
- `_generate_import_statement()` :1725
- `_generate_assignment()` :1766
- `_generate_other_node()` :1825
- `_generate_statement_from_node()` :2047
- `_generate_expression_code()` :2428
- `_extract_op_symbol()` :2629
- `_extract_unary_op_symbol()` :2643
- `_extract_compare_op_symbol()` :2654
- `_extract_argument_name()` :2669
- `_extract_defaults_from_function()` :2707
- `_extract_defaults_from_code_obj()` :2747
- `_extract_defaults_from_consts()` :2793
- `_extract_defaults_from_ast_args()` :2834
- `_extract_decorator_name()` :2867
- `_extract_decorator_with_params()` :2925
- `_extract_node_name()` :2972
- `_is_async_function()` :3233
- `_is_internal_expr()` :3266
- `_generate_async_function()` :3288
- `_generate_subscript_expression()` :3305
- `_generate_await_expression()` :3326
- `_generate_list_comprehension()` :3340
- `_generate_dict_comprehension()` :3376
- `_generate_lambda_expression()` :3403
- `_generate_generator_expression()` :3441
- `_generate_async_for()` :3466
- `_generate_async_with()` :3495
- `_generate_match_statement()` :3523
- `_analyze_code_quality()` :3548
- `_generate_enhanced_decorators()` :3638
- `_generate_function_code()` :3668
- `_generate_lambda_code()` :3798
- `_generate_function_body_from_bytecode()` :3837
- `_extract_return_value()` :3923
- `_post_process_pattern_matching()` :4078
- `_generate_statement()` :4097
- `_generate_if_statement()` :4458
- `_generate_if_elif_statement()` :4610
- `_generate_if_statement_from_dict()` :4685
- `_generate_for_statement_from_dict()` :4757
- `_generate_while_statement_from_dict()` :4796
- `_generate_expr_from_dict()` :4832
- `_generate_for_statement()` :4910
- `_generate_while_statement()` :4981
- `_generate_try_statement()` :5045
- `_generate_except_handler()` :5113
- `_generate_with_statement()` :5162
- `_generate_raise_statement()` :5219
- `_simplify_expression()` :5234
- `_generate_block()` :5265
- `_generate_block_from_nodes()` :5296
- `_optimize_block_nodes()` :5309
- `_format_code()` :5389
- `_simple_format_code()` :5402
- `visit()` :5473
- `default_visit()` :5502
- `_extract_function_body_from_bytecode()` :5578
- `_generate_statement_legacy()` :5738
- `_trace_bytecode_value()` :5795
- `add_token()` :5865
- `new_line()` :5898
- `new_line_no_indent()` :5930
- `_get_expr_str()` :5962
- `add_line()` :5987
- `add_empty_line()` :5993
- `flush_line()` :5999
- `visit_ASTBlock()` :6005
- `visit_ASTIf()` :6026
- `_is_return_none()` :6137
- `_visit_elif_chain()` :6172
- `visit_ASTFor()` :6251
- `visit_ASTWhile()` :6357
- `visit_ASTReturn()` :6415
- `visit_ASTUnary()` :6441
- `visit_ASTUnaryOp()` :6445
- `_visit_unary_node()` :6449
- `visit_ASTTry()` :6469
- `visit_ASTRaise()` :6540
- `visit_ASTObject()` :6549
- `visit_ASTExpr()` :6612
- `visit_ASTCall()` :6619
- `visit_ASTBinary()` :6735
- `_get_operator_symbol()` :6749
- `_generate_expr()` :6778
- `visit_ASTYield()` :7752
- `visit_ASTCompare()` :7764
- `visit_ASTBinary()` :7804
- `visit_ASTModule()` :7850
- `visit_ASTFunctionDef()` :7883
- `_generate_test_function_body()` :7989
- `_generate_simple_function_body()` :8006
- `_generate_function_body_from_code_obj()` :8023
- `_generate_complete_function_body()` :8065
- `_has_control_flow_instructions()` :8144
- `_analyze_bytecode_for_function_body()` :8161
- `_analyze_simple_bytecode()` :8200
- `_disassemble_bytecode()` :8224
- `_generate_body_from_ast()` :8249
- `visit_ASTDecoratorApplication()` :8265
- `visit_ASTClassDef()` :8284
- `visit_ASTImport()` :8351
- `visit_ASTImportFrom()` :8376
- `visit_ASTName()` :8392
- `visit_ASTConstant()` :8405
- `visit_ASTAssign()` :8454
- `visit_ASTStore()` :8464
- `visit_ASTListComp()` :8509
- `visit_ASTSetComp()` :8531
- `visit_ASTDictComp()` :8553
- `visit_ASTGenExpr()` :8577
- `_generate_comprehension()` :8599

## 相关页面

- [[parsers-code-generator|parsers/code_generator.py]]
- [[index|Wiki Index]]
